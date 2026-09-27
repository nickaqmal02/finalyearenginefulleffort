# chat_analyzer/services/upload_service.py
from __future__ import annotations
import hashlib
import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from django.db import transaction
from chat_analyzer.models import Conversation, UploadHistory, User, ClientContact
from chat_analyzer.services.text_cleaner import get_cleaner
from chat_analyzer.services.whatsapp_parser import parse_whatsapp_content
from chat_analyzer.services.sentiment_analyzer import analyze_sentiment

if TYPE_CHECKING:
    from django.core.files.uploadedfile import UploadedFile


def _normalize(value: str) -> str:
    """Normalize a name/phone for comparison: lowercase, strip symbols."""
    if not value:
        return ""
    value = value.lower()
    return "".join(ch for ch in value if ch.isalnum())


def _find_sender(username: str, client: User) -> User | None:
    """
    Match a WhatsApp sender to User, in priority order:
    1. Phone number (User.phone or ClientContact.phone_number)
    2. Full name (client's names or any parent contact name)
    3. Substring (sender name appears inside a user's full name)
    """
    sender_key = _normalize(username)
    if not sender_key:
        return None

    # 1. match by phone number
    phone_to_user: dict[str, User] = {}
    for u in User.objects.filter(phone__isnull=False).exclude(phone=""):
        key = _normalize(u.phone)
        if key:
            phone_to_user[key] = u

    for contact in ClientContact.objects.select_related("client"):
        key = _normalize(contact.phone_number)
        if key:
            phone_to_user[key] = contact.client

    if sender_key in phone_to_user:
        return phone_to_user[sender_key]

    # 2. match by full name
    client_key = _normalize(
        (client.first_name or "") + (client.last_name or "")
    )
    if client_key and sender_key == client_key:
        return client

    contacts = ClientContact.objects.filter(client=client)
    for contact in contacts:
        if sender_key == _normalize(contact.name):
            return client

    # 3. match by substring (sender name inside a full name)
    if client_key and (sender_key in client_key or client_key in sender_key):
        return client
    for contact in contacts:
        ckey = _normalize(contact.name)
        if ckey and (sender_key in ckey or ckey in sender_key):
            return client

    # therapist / doctor by full name
    for staff in User.objects.filter(role__in=["therapist", "doctor"]):
        staff_key = _normalize(
            (staff.first_name or "") + (staff.last_name or "")
        )
        if staff_key and (sender_key == staff_key or sender_key in staff_key):
            return staff

    return None


def process_whatsapp_upload(
    file_path_or_file: str | "UploadedFile",
    client_id: int,
    uploader_id: int | None = None,
    batch_id: str | None = None,
    chat_type: str = "individual",
    dry_run: bool = False,
) -> dict[str, object]:
    """
    Shared upload engine — parse, clean, sentiment, save.

    Accepts either a file path string (CLI) or an UploadedFile object (admin form).
    Topic training happens separately via train_topics() — caller orchestrates.

    Returns a results dict with keys:
        saved, duplicates, unmatched, positive, negative, neutral,
        batch_id, total, file_name
    Or error/dry_run keys on early exit.
    """
    # 1. Get client + uploader
    try:
        client = User.objects.get(id=client_id, role="client")
    except User.DoesNotExist:
        return {"error": f"Client with ID {client_id} not found"}

    uploader = None
    if uploader_id:
        try:
            uploader = User.objects.get(id=uploader_id)
            if uploader.role == "client":
                return {"error": "Clients cannot upload chats"}
        except User.DoesNotExist:
            pass
    if uploader is None:
        uploader = User.objects.filter(username="admin").first()

    # 2. Read content (path OR UploadedFile)
    if hasattr(file_path_or_file, "read"):
        content = file_path_or_file.read().decode("utf-8")
        file_name = file_path_or_file.name
    else:
        with open(file_path_or_file, "r", encoding="utf-8") as f:
            content = f.read()
        file_name = file_path_or_file.split("/")[-1]

    # 3. Parse
    messages = parse_whatsapp_content(content)
    if not messages:
        return {"error": "No messages found in file", "file_name": file_name}

    if dry_run:
        return {
            "dry_run": True,
            "message_count": len(messages),
            "file_name": file_name,
        }

    # 4. Clean + sentiment + save
    cleaner = get_cleaner()
    with transaction.atomic():
        upload_history = UploadHistory.objects.create(
            uploaded_by=uploader,
            file_name=file_name,
            batch_id=batch_id or str(uuid.uuid4())[:8],
            status="processing",
        )

        saved = 0
        duplicates = 0
        unmatched = 0
        pos = 0
        neg = 0
        neu = 0

        for msg in messages:
            # hash for deduplication
            text = f"{client_id}{msg['date']}{msg['username']}{msg['message']}"
            message_hash = hashlib.sha256(text.encode()).hexdigest()

            if Conversation.objects.filter(message_hash=message_hash).exists():
                duplicates += 1
                continue

            # dual cleaning
            cleaned_sentiment = cleaner.clean_for_sentiment(msg["message"])
            cleaned_topic = cleaner.clean_for_topic_modeling(msg["message"])

            # sentiment analysis
            sentiment = analyze_sentiment(cleaned_sentiment)
            if sentiment["label"] == "positive":
                pos += 1
            elif sentiment["label"] == "negative":
                neg += 1
            else:
                neu += 1

            # build conversation row
            conversation = Conversation(
                client=client,
                date=msg["date"],
                time=msg["time"],
                username=msg["username"],
                message=msg["message"],
                cleaned_text=cleaned_sentiment,
                cleaned_text_topic=cleaned_topic,
                is_cleaned_sentiment=True,
                is_cleaned_topic=True,
                message_hash=message_hash,
                sentiment=sentiment["label"],
                sentiment_score=sentiment["score"],
                sentiment_confidence=sentiment["confidence"],
                upload_batch=upload_history.batch_id,
                upload_history=upload_history,
                uploaded_by=uploader,
                uploaded_at=datetime.now(),
                is_processed=True,
                chat_type=chat_type,
            )

            # sender matching
            sender = _find_sender(msg["username"], client)
            if sender:
                conversation.sender = sender
                conversation.is_from_client = (sender.id == client.id)
            else:
                unmatched += 1

            conversation.save()
            saved += 1

        # update upload history
        upload_history.message_count = saved + duplicates
        upload_history.matched_count = saved
        upload_history.unmatched_count = unmatched
        upload_history.duplicate_count = duplicates
        upload_history.positive_count = pos
        upload_history.negative_count = neg
        upload_history.neutral_count = neu
        upload_history.status = "success"
        upload_history.save()

    return {
        "saved": saved,
        "duplicates": duplicates,
        "unmatched": unmatched,
        "positive": pos,
        "negative": neg,
        "neutral": neu,
        "batch_id": upload_history.batch_id,
        "total": len(messages),
        "file_name": file_name,
    }