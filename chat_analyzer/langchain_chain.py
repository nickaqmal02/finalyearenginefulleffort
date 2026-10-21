"""
LangChain-powered reservation chatbot for Sentiri.

Replaces the n8n AI Agent with a direct LangChain ConversationChain.
GLM 5.3 via rootsys.cloud (OpenAI-compatible, Chat Completions API only).
Conversation memory persisted in Redis keyed by client_id.

Flow:
  1. User sends message → reservation_ask view calls get_reservation_reply()
  2. LangChain ConversationChain generates a natural reply
  3. If the user confirms a booking, we call the Django APIs directly
"""
import os
import re
import json
import requests
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_classic.chains import ConversationChain
from langchain_classic.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.prompts import PromptTemplate


# ── Config ──
ROOTSYS_API_KEY = "fiq-26561a77461073dc85b6f49b4557e454"
ROOTSYS_BASE_URL = "https://rootsys.cloud/v1"
MODEL_NAME = "glm-5.3"
REDIS_URL = "redis://localhost:6379/0"
DJANGO_API_BASE = "http://localhost:8000/api"

# ── System prompt for the reservation assistant ──
RESERVATION_PROMPT = """You are Sentiri, a friendly and efficient reservation assistant for an autism therapy center in Malaysia.

Conversation history:
{history}

Current user message: {input}

INSTRUCTIONS:
- You MUST remember details from the conversation history above. Do NOT re-ask for information the user already provided.
- If the user already mentioned a therapist name, date, or time in previous messages, DO NOT ask for it again.
- Only ask for information that is still missing.
- When the user says a name (e.g., "Farah", "Aina"), they are naming the THERAPIST they want to see, not their own name.
- When the user says a date (e.g., "26 October", "next Tuesday"), that is their preferred booking date.
- When the user says a time (e.g., "1500", "3pm", "10:00"), that is their preferred time.
- If the user hasn't chosen a therapist yet, mention the available therapists from the context and ask which one they'd like.
- If the client has an assigned therapist, suggest them first but let the user choose any available therapist.
- The context shows each therapist's working days. If the user asks who works on a certain day, check the context and tell them.
- If the user picks a date that falls on a day when their chosen therapist doesn't work, suggest alternative therapists who DO work on that day.
- Once you have therapist + date + time, confirm all three details and ask: "Shall I go ahead and book this? (yes/no)"
- If the user confirms (says "yes", "confirm", "book it"), just say "BOOKING_PENDING" and list the therapist, date, and time. Do NOT say BOOKING_CONFIRMED — the system will check availability and confirm.
- If the user says "no" or wants to change something, acknowledge and ask what they'd like to change.
- Be concise — 1-3 sentences max. Use simple, clear language suitable for autism therapy clients.

Reply:"""


def _get_llm():
    """Create a ChatOpenAI instance pointing to rootsys.cloud."""
    # Set env var so ChatOpenAI picks it up (it requires SecretStr type)
    os.environ["OPENAI_API_KEY"] = ROOTSYS_API_KEY
    return ChatOpenAI(
        model=MODEL_NAME,
        base_url=ROOTSYS_BASE_URL,
        temperature=0.3,
        max_retries=2,
    )


def _get_chain(client_id):
    """Build a ConversationChain with Redis-backed memory for this client.

    Memory is keyed by client_id so each client has their own conversation thread.
    """
    session_key = f"sentiri-reservation-{client_id}"

    message_history = RedisChatMessageHistory(
        session_id=session_key,
        url=REDIS_URL,
    )

    memory = ConversationBufferMemory(
        chat_memory=message_history,
        memory_key="history",
        input_key="input",
        return_messages=False,
    )

    llm = _get_llm()

    prompt = PromptTemplate(
        input_variables=["history", "input"],
        template=RESERVATION_PROMPT,
    )

    chain = ConversationChain(
        llm=llm,
        memory=memory,
        prompt=prompt,
        verbose=False,
    )

    return chain


def get_reservation_reply(message, client_id, staff_id=None):
    """Send a message to the reservation chatbot and get a reply.

    Args:
        message: The user's message text.
        client_id: The logged-in client's user ID (for memory session).
        staff_id: The client's assigned therapist ID (optional, for context).

    Returns:
        dict with keys:
            - reply: The chatbot's text reply
            - booking_confirmed: bool — whether the user confirmed a booking
            - booking_details: dict — extracted therapist/date/time if confirmed
    """
    chain = _get_chain(client_id)

    # Build context with available therapists + their working days
    from django.contrib.auth import get_user_model
    from .models import StaffSchedule
    User = get_user_model()
    therapists = User.objects.filter(role__in=["therapist", "doctor"], is_active=True)

    DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    therapist_infos = []
    for t in therapists:
        schedules = StaffSchedule.objects.filter(staff=t, is_available=True).order_by('day_of_week')
        working_days = ", ".join([DAYS[s.day_of_week] for s in schedules]) if schedules else "No set schedule"
        therapist_infos.append(f"{t.get_full_name()} (ID: {t.id}, works: {working_days})")
    therapist_list = "; ".join(therapist_infos)

    # Get client's assigned therapist name
    assigned_therapist_name = ""
    if staff_id:
        try:
            therapist = User.objects.get(id=staff_id)
            assigned_therapist_name = therapist.get_full_name()
        except User.DoesNotExist:
            pass

    context_parts = [f"[Available therapists: {therapist_list}]"]
    if assigned_therapist_name:
        context_parts.append(f"[Client's assigned therapist: {assigned_therapist_name} (ID: {staff_id})]")

    # Pass today's date
    from django.utils import timezone
    today = timezone.now().date()
    today_str = today.strftime("%A, %d %B %Y")
    context_parts.append(f"[Today is: {today_str}]")

    # If the user mentioned a date, calculate the weekday for them
    # Also check recent conversation history for dates (user might reference a previously mentioned date)
    import re as _re
    full_recent_text = message + " " + " ".join([
        m.content if hasattr(m, 'content') else str(m)
        for m in chain.memory.chat_memory.messages[-4:]
    ])
    date_match = _re.search(r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December))', full_recent_text, _re.IGNORECASE)
    if date_match:
        try:
            raw_date = date_match.group(1)
            parsed_date = _parse_date(raw_date)
            if parsed_date:
                dt = datetime.strptime(parsed_date, "%Y-%m-%d")
                weekday_name = dt.strftime('%A')
                # Check which therapists work on that day
                weekday_num = dt.weekday()
                DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                working = []
                not_working = []
                for t in therapists:
                    sched = StaffSchedule.objects.filter(staff=t, day_of_week=weekday_num).first()
                    if sched and sched.is_available:
                        working.append(t.get_full_name())
                    else:
                        not_working.append(t.get_full_name())
                context_parts.append(f"[Note: {raw_date} = {weekday_name}]")
                context_parts.append(f"[Therapists working on {weekday_name}: {', '.join(working) if working else 'NONE'}]")
                if not_working:
                    context_parts.append(f"[Therapists NOT working on {weekday_name}: {', '.join(not_working)}]")
        except Exception:
            pass

    context_parts.append(message)
    context_message = "\n".join(context_parts)

    reply = chain.predict(input=context_message)

    # Check if the bot says booking is pending (user confirmed, system needs to check)
    booking_pending = "BOOKING_PENDING" in reply.upper()

    booking_details = {}
    if booking_pending:
        # Extract details from the conversation/memory
        booking_details = _extract_booking_details(chain, client_id)

        # Clean up the reply — remove the BOOKING_PENDING marker
        reply = reply.replace("BOOKING_PENDING", "").strip()

        # Actually make the booking via Django API — only confirmed if API succeeds
        booking_confirmed = False
        if booking_details.get("staff_id") and booking_details.get("date") and booking_details.get("time"):
            booking_result = _call_book_session(
                client_id=client_id,
                staff_id=booking_details["staff_id"],
                date_str=booking_details["date"],
                time_str=booking_details["time"],
            )
            if booking_result.get("success"):
                booking_confirmed = True
                reply = f"✅ Booking confirmed! {booking_result.get('message', '')}"
                # Fire instant notification to therapist
                booking_id = booking_result.get("booking_id")
                if booking_id:
                    try:
                        from .tasks import create_booking_notification
                        create_booking_notification.delay(booking_id)
                    except Exception:
                        pass  # don't fail the reply if notification fails
            else:
                booking_confirmed = False
                reply = f"⚠️ Booking could not be completed: {booking_result.get('reason', 'Unknown error')}"
        else:
            booking_confirmed = False
            reply = f"⚠️ I couldn't extract all the booking details. Could you please confirm the therapist name, date, and time?"
    else:
        booking_confirmed = False

    return {
        "reply": reply,
        "booking_confirmed": booking_confirmed,
        "booking_details": booking_details,
    }


def _extract_booking_details(chain, client_id):
    """Try to extract therapist name, date, and time from conversation memory."""
    details = {}

    try:
        messages = chain.memory.chat_memory.messages

        # Only search the LAST 6 messages (current booking flow)
        recent_messages = messages[-6:] if len(messages) > 6 else messages

        # Build text from AI messages only (they contain the bot's understanding)
        # Human messages contain the context prefix with ALL therapist names — skip those
        ai_messages = [m for m in recent_messages if getattr(m, 'type', '') == 'ai']

        # For therapist extraction: use only the LAST AI message (the BOOKING_PENDING one)
        # Previous AI messages may list all therapists in a welcome message
        if ai_messages:
            booking_text = ai_messages[-1].content if hasattr(ai_messages[-1], 'content') else str(ai_messages[-1])
        else:
            booking_text = ""

        # For date/time extraction: use all recent AI messages
        full_text = " ".join([
            m.content if hasattr(m, "content") else str(m)
            for m in ai_messages
        ])

        # Extract therapist name — search only the BOOKING_PENDING message
        from django.contrib.auth import get_user_model
        User = get_user_model()
        therapists = User.objects.filter(role__in=["therapist", "doctor"])
        for t in therapists:
            full_name = t.get_full_name().lower()
            first_name = full_name.split()[0] if full_name else ""
            if first_name and first_name in booking_text.lower():
                details["staff_id"] = t.id
                details["staff_name"] = t.get_full_name()
                break

        # Extract date — look for patterns like "26 October", "2026-10-26", "Oct 26"
        # Use findall and take the LAST match (in case of multiple dates in history)
        date_patterns = [
            r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December))',
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
        ]
        for pattern in date_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            if matches:
                # Take the last match — it's the most recent date mentioned
                raw_date = matches[-1] if isinstance(matches[-1], str) else matches[-1][0]
                parsed = _parse_date(raw_date)
                if parsed:
                    details["date"] = parsed
                    break

        # Extract time — look for patterns like "1500", "15:00", "3pm", "10:00"
        # Order matters: 4-digit military time first, then HH:MM, then am/pm
        # Key: skip years (20xx) by checking context — times appear after "at" or with H suffix
        time_patterns = [
            r'(?:at\s)?(\d{4})\s*(?:hours?|H)\b',           # "1500H", "at 1500 hours"
            r'(?:at\s)(\d{4})(?!\d)',                        # "at 1500" — only match 4-digit after "at"
            r'(?<!:)\b(\d{1,2})\s*(am|pm)\b',                # "3pm", "10 am" — NOT "00 PM" from "3:00 PM"
            r'\b(\d{1,2}:\d{2})\s*(am|pm)?',                 # 15:00, 3:00 pm (fallback)
        ]
        for pattern in time_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            if matches:
                # Take the LAST match — it's the most recent time mentioned
                last = matches[-1]
                if isinstance(last, tuple):
                    raw_time = last[0]
                    if len(last) > 1 and last[1]:
                        raw_time = f"{last[0]} {last[1]}"
                else:
                    raw_time = last
                parsed = _parse_time(raw_time)
                if parsed:
                    details["time"] = parsed
                    break

    except Exception as e:
        print(f"[langchain_chain] Error extracting details: {e}")

    return details


def _parse_date(raw):
    """Parse various date formats to YYYY-MM-DD."""
    try:
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d %B", "%d %b"]:
            try:
                dt = datetime.strptime(raw, fmt)
                # For dates without year, assume current year
                if fmt in ["%d %B", "%d %b"]:
                    from datetime import date
                    dt = dt.replace(year=date.today().year)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
    except Exception:
        pass
    return None


def _parse_time(raw):
    """Parse various time formats to HH:MM."""
    try:
        raw = raw.strip()
        # 1500 or 1500H — 4-digit military time
        match = re.match(r'^(\d{4})\s*(?:hours?|H)?$', raw, re.IGNORECASE)
        if match:
            digits = match.group(1)
            hh, mm = int(digits[:2]), int(digits[2:])
            # Validate it's a real time (not a year like 2026)
            if 0 <= hh <= 23 and 0 <= mm <= 59:
                return f"{hh:02d}:{mm:02d}"
            return None
        # 15:00
        if re.match(r'^\d{1,2}:\d{2}$', raw):
            parts = raw.split(":")
            return f"{int(parts[0]):02d}:{parts[1]}"
        # 12:00 PM / 3:00 pm — HH:MM with am/pm suffix
        match = re.match(r'^(\d{1,2}):(\d{2})\s*(am|pm)$', raw, re.IGNORECASE)
        if match:
            hour = int(match.group(1))
            minute = match.group(2)
            if match.group(3).lower() == "pm" and hour != 12:
                hour += 12
            if match.group(3).lower() == "am" and hour == 12:
                hour = 0
            return f"{hour:02d}:{minute}"
        # 3pm / 3 pm / 3PM
        match = re.match(r'^(\d{1,2})\s*(am|pm)$', raw, re.IGNORECASE)
        if match:
            hour = int(match.group(1))
            if match.group(2).lower() == "pm" and hour != 12:
                hour += 12
            if match.group(2).lower() == "am" and hour == 12:
                hour = 0
            return f"{hour:02d}:00"
    except Exception:
        pass
    return None


def _call_book_session(client_id, staff_id, date_str, time_str):
    """Call the Django book-session API to create a booking."""
    try:
        response = requests.post(
            f"{DJANGO_API_BASE}/book-session/",
            json={
                "client_id": client_id,
                "staff_id": staff_id,
                "date": date_str,
                "time": time_str,
            },
            timeout=10,
        )
        return response.json()
    except Exception as e:
        return {"success": False, "reason": str(e)}


def clear_conversation(client_id):
    """Clear the conversation memory for a client (start fresh)."""
    session_key = f"sentiri-reservation-{client_id}"
    try:
        history = RedisChatMessageHistory(
            session_id=session_key,
            url=REDIS_URL,
        )
        history.clear()
        return True
    except Exception as e:
        print(f"[langchain_chain] Error clearing memory: {e}")
        return False
