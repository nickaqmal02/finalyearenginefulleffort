"""JSON API endpoints for the n8n reservation chatbot.

These are NOT Django template views — they return JSON only.
n8n's AI Agent node calls them as "tools" via HTTP.

Endpoints:
  1. POST /api/check-availability/   → "Is this date+time free?"
  2. POST /api/book-session/         → "Book this slot"
  3. GET  /api/list-sessions/         → "What are my upcoming bookings?"
  4. GET  /api/staff-schedule/        → "When does this staff member work?"
"""
import json
from datetime import datetime, date, time, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import StaffSchedule, StaffTimeOff, SessionBooking

User = get_user_model()


@csrf_exempt
@require_http_methods(["POST"])
def check_availability(request):
    """Check if a staff member is available at a given date+time.

    Called by n8n when the LLM detects a booking request.
    3-layer check: office hours → time off → slot conflict.

    Expects JSON body:
    {
        "staff_id": 4,           // therapist or doctor ID
        "date": "2026-10-21",    // YYYY-MM-DD
        "time": "15:00"          // HH:MM
    }

    Returns:
    {
        "available": true/false,
        "reason": "...",        // why not available (if false)
        "staff_name": "Aina Razak",
        "date": "2026-10-21",
        "time": "15:00"
    }
    """
    try:
        data = json.loads(request.body)
        staff_id = data.get("staff_id")
        date_str = data.get("date")
        time_str = data.get("time")

        if not all([staff_id, date_str, time_str]):
            return JsonResponse({
                "available": False,
                "reason": "Missing required fields: staff_id, date, time"
            }, status=400)

        # Parse inputs
        staff = User.objects.get(id=staff_id, role__in=["therapist", "doctor"])
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        target_time = datetime.strptime(time_str, "%H:%M").time()
        weekday = target_date.weekday()  # Monday=0, Sunday=6

        # ── LAYER 1: Office hours ──
        # Is there a StaffSchedule for this staff on this weekday?
        try:
            schedule = StaffSchedule.objects.get(staff=staff, day_of_week=weekday)
        except StaffSchedule.DoesNotExist:
            return JsonResponse({
                "available": False,
                "reason": f"{staff.get_full_name()} does not work on {target_date.strftime('%A')}.",
                "staff_name": staff.get_full_name(),
                "date": date_str,
                "time": time_str,
            })

        if not schedule.is_available:
            return JsonResponse({
                "available": False,
                "reason": f"{staff.get_full_name()} is off every {target_date.strftime('%A')}.",
                "staff_name": staff.get_full_name(),
                "date": date_str,
                "time": time_str,
            })

        # Check if the requested time is within office hours
        if not (schedule.start_time <= target_time <= schedule.end_time):
            return JsonResponse({
                "available": False,
                "reason": f"Office hours are {schedule.start_time.strftime('%H:%M')}-{schedule.end_time.strftime('%H:%M')}. Requested time {time_str} is outside.",
                "staff_name": staff.get_full_name(),
                "date": date_str,
                "time": time_str,
            })

        # ── LAYER 2: Specific date exception (sick leave, holiday) ──
        time_off = StaffTimeOff.objects.filter(staff=staff, date=target_date).first()
        if time_off:
            reason = time_off.reason or "not available"
            return JsonResponse({
                "available": False,
                "reason": f"{staff.get_full_name()} is off on {date_str} ({reason}).",
                "staff_name": staff.get_full_name(),
                "date": date_str,
                "time": time_str,
            })

        # ── LAYER 3: Slot conflict (staff side) ──
        # 1-hour session: target_time → target_time + 1hr
        # Overlap check: two ranges overlap if start_A < end_B AND start_B < end_A
        from datetime import timedelta as td
        from datetime import datetime as dt
        target_end = (dt.combine(date.today(), target_time) + td(hours=1)).time()

        staff_conflict = SessionBooking.objects.filter(
            staff=staff,
            date=target_date,
            status__in=["pending", "confirmed"],
            start_time__lt=target_end,   # existing starts before new ends
            end_time__gt=target_time,    # existing ends after new starts
        ).exists()

        if staff_conflict:
            return JsonResponse({
                "available": False,
                "reason": f"{staff.get_full_name()} already has a session overlapping {time_str} on {date_str}.",
                "staff_name": staff.get_full_name(),
                "date": date_str,
                "time": time_str,
            })

        # ── LAYER 4: Slot conflict (client side) ──
        # No overlap: a client can't have two sessions at the same time,
        # even with different staff members.
        # n8n calls this API without Django auth, so we use client_id from the body
        client_id_from_body = data.get("client_id")
        client_conflict = False
        if client_id_from_body:
            from chat_analyzer.models import User as UserModel
            try:
                client_user = UserModel.objects.get(id=client_id_from_body, role="client")
                client_conflict = SessionBooking.objects.filter(
                    client=client_user,
                    date=target_date,
                    status__in=["pending", "confirmed"],
                    start_time__lt=target_end,
                    end_time__gt=target_time,
                ).exists()
            except UserModel.DoesNotExist:
                pass

        if client_conflict:
            return JsonResponse({
                "available": False,
                "reason": f"The client already has a session overlapping {time_str} on {date_str}.",
                "staff_name": staff.get_full_name(),
                "date": date_str,
                "time": time_str,
            })

        # ✅ All 3 layers passed — slot is available
        return JsonResponse({
            "available": True,
            "reason": "Slot is available.",
            "staff_name": staff.get_full_name(),
            "date": date_str,
            "time": time_str,
        })

    except User.DoesNotExist:
        return JsonResponse({
            "available": False,
            "reason": f"Staff with ID {staff_id} not found."
        }, status=404)
    except ValueError as e:
        return JsonResponse({
            "available": False,
            "reason": f"Invalid date/time format: {str(e)}"
        }, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def book_session(request):
    """Create a session booking.

    Called by n8n when the client confirms they want to book.
    Runs the same 3-layer check first, then creates the booking.

    Expects JSON body:
    {
        "client_id": 10,
        "staff_id": 4,
        "date": "2026-10-21",
        "time": "15:00"
    }

    Returns:
    {
        "success": true,
        "booking_id": 42,
        "message": "Booked with Aina Razak on 2026-10-21 at 15:00."
    }
    """
    try:
        data = json.loads(request.body)
        client_id = data.get("client_id")
        staff_id = data.get("staff_id")
        date_str = data.get("date")
        time_str = data.get("time")

        if not all([client_id, staff_id, date_str, time_str]):
            return JsonResponse({
                "success": False,
                "reason": "Missing required fields: client_id, staff_id, date, time"
            }, status=400)

        # Validate users
        client = User.objects.get(id=client_id, role="client")
        staff = User.objects.get(id=staff_id, role__in=["therapist", "doctor"])
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        target_time = datetime.strptime(time_str, "%H:%M").time()
        weekday = target_date.weekday()

        # ── Re-run all 3 layers before booking ──
        # Layer 1 — check schedule exists
        try:
            schedule = StaffSchedule.objects.get(staff=staff, day_of_week=weekday)
        except StaffSchedule.DoesNotExist:
            return JsonResponse({
                "success": False,
                "reason": f"{staff.get_full_name()} does not work on {target_date.strftime('%A')}."
            })

        # Check if this day is available (not a regular day off)
        if not schedule.is_available:
            return JsonResponse({
                "success": False,
                "reason": f"{staff.get_full_name()} does not work on {target_date.strftime('%A')}s."
            })

        # Check if requested time is within office hours
        if not (schedule.start_time <= target_time <= schedule.end_time):
            return JsonResponse({
                "success": False,
                "reason": f"Time {time_str} is outside office hours ({schedule.start_time.strftime('%H:%M')}-{schedule.end_time.strftime('%H:%M')})."
            })

        # Layer 2
        if StaffTimeOff.objects.filter(staff=staff, date=target_date).exists():
            return JsonResponse({
                "success": False,
                "reason": f"{staff.get_full_name()} is off on {date_str}."
            })

        # Layer 3 — slot conflict (staff side, proper overlap check)
        target_end = (datetime.combine(date.today(), target_time) + timedelta(hours=1)).time()
        if SessionBooking.objects.filter(
            staff=staff, date=target_date,
            start_time__lt=target_end, end_time__gt=target_time,
            status__in=["pending", "confirmed"],
        ).exists():
            return JsonResponse({
                "success": False,
                "reason": f"{staff.get_full_name()} has a session overlapping {time_str} on {date_str}."
            })

        # Layer 4 — slot conflict (client side, no double-booking)
        if SessionBooking.objects.filter(
            client=client, date=target_date,
            start_time__lt=target_end, end_time__gt=target_time,
            status__in=["pending", "confirmed"],
        ).exists():
            return JsonResponse({
                "success": False,
                "reason": f"The client already has a session overlapping {time_str} on {date_str}."
            })

        # ✅ Create the booking (1-hour session)
        end_time = target_end
        booking = SessionBooking.objects.create(
            client=client,
            staff=staff,
            date=target_date,
            start_time=target_time,
            end_time=end_time,
            status="confirmed",
        )

        return JsonResponse({
            "success": True,
            "booking_id": booking.id,
            "message": f"Booked with {staff.get_full_name()} on {date_str} at {time_str}.",
            "staff_name": staff.get_full_name(),
            "date": date_str,
            "time": time_str,
        })

    except User.DoesNotExist as e:
        return JsonResponse({
            "success": False,
            "reason": f"User not found: {str(e)}"
        }, status=404)
    except ValueError as e:
        return JsonResponse({
            "success": False,
            "reason": f"Invalid format: {str(e)}"
        }, status=400)


@csrf_exempt
@require_http_methods(["GET"])
def list_sessions(request):
    """List upcoming sessions for a client.

    Called by n8n when the client asks "what are my bookings?"

    Expects query params: ?client_id=10

    Returns:
    {
        "sessions": [
            {
                "id": 42,
                "staff_name": "Aina Razak",
                "date": "2026-10-21",
                "time": "15:00",
                "status": "confirmed"
            }
        ],
        "count": 1
    }
    """
    try:
        client_id = request.GET.get("client_id")
        if not client_id:
            return JsonResponse({
                "sessions": [],
                "count": 0,
                "reason": "Missing client_id parameter"
            }, status=400)

        client = User.objects.get(id=client_id, role="client")
        today = date.today()

        bookings = SessionBooking.objects.filter(
            client=client,
            date__gte=today,
            status__in=["pending", "confirmed"],
        ).select_related("staff").order_by("date", "start_time")

        sessions = []
        for b in bookings:
            sessions.append({
                "id": b.id,
                "staff_name": b.staff.get_full_name(),
                "date": b.date.strftime("%Y-%m-%d"),
                "time": b.start_time.strftime("%H:%M"),
                "status": b.status,
            })

        return JsonResponse({
            "sessions": sessions,
            "count": len(sessions),
        })

    except User.DoesNotExist:
        return JsonResponse({
            "sessions": [],
            "count": 0,
            "reason": f"Client with ID {client_id} not found."
        }, status=404)


@csrf_exempt
@require_http_methods(["GET"])
def staff_schedule(request):
    """Get a staff member's weekly schedule.

    Called by n8n when the client asks "when is Aina available?"

    Expects query params: ?staff_id=4

    Returns:
    {
        "staff_name": "Aina Razak",
        "schedule": [
            {"day": "Monday", "start": "09:00", "end": "17:00", "available": true},
            ...
        ]
    }
    """
    try:
        staff_id = request.GET.get("staff_id")
        if not staff_id:
            return JsonResponse({
                "reason": "Missing staff_id parameter"
            }, status=400)

        staff = User.objects.get(id=staff_id, role__in=["therapist", "doctor"])
        schedules = StaffSchedule.objects.filter(staff=staff).order_by("day_of_week")

        days = []
        for s in schedules:
            days.append({
                "day": s.get_day_of_week_display(),
                "start": s.start_time.strftime("%H:%M"),
                "end": s.end_time.strftime("%H:%M"),
                "available": s.is_available,
            })

        return JsonResponse({
            "staff_name": staff.get_full_name(),
            "schedule": days,
        })

    except User.DoesNotExist:
        return JsonResponse({
            "reason": f"Staff with ID {staff_id} not found."
        }, status=404)


@csrf_exempt
@require_http_methods(["POST"])
def n8n_callback(request):
    """Receives the AI Agent's reply from n8n after processing.

    n8n calls this endpoint via the Callback to Django HTTP node.
    Stores the reply in a temp file keyed by client_id.
    """
    import json as _json
    import os
    from django.utils import timezone
    data = _json.loads(request.body)
    reply = data.get('reply', '')
    client_id = data.get('client_id', 'unknown')

    # Write to temp file — Django's reservation_ask polls for this
    filepath = f'/tmp/n8n_reply_{client_id}.json'
    with open(filepath, 'w') as f:
        _json.dump({'reply': reply, 'timestamp': str(timezone.now())}, f)

    return JsonResponse({'status': 'received'})


@csrf_exempt
@require_http_methods(["GET"])
def poll_reply(request):
    """Frontend polls this to check if n8n's AI reply is ready.

    Expects: ?client_id=12
    Returns: {"ready": true, "reply": "..."} or {"ready": false}
    """
    import os
    client_id = request.GET.get("client_id")
    if not client_id:
        return JsonResponse({"ready": False, "reason": "Missing client_id"})

    reply_file = f"/tmp/n8n_reply_{client_id}.json"
    if os.path.exists(reply_file):
        import json as _json
        with open(reply_file) as f:
            data = _json.load(f)
        os.remove(reply_file)
        return JsonResponse({"ready": True, "reply": data.get("reply", "")})
    
    return JsonResponse({"ready": False})


@csrf_exempt
@require_http_methods(["POST"])
def cancel_booking(request):
    """Cancel a session booking.

    Expects JSON body:
    {
        "booking_id": 42,
        "client_id": 10
    }

    Returns:
    {
        "success": true,
        "message": "Booking cancelled."
    }
    """
    try:
        data = json.loads(request.body)
        booking_id = data.get("booking_id")
        client_id = data.get("client_id")

        if not booking_id or not client_id:
            return JsonResponse({
                "success": False,
                "reason": "Missing required fields: booking_id, client_id"
            }, status=400)

        booking = SessionBooking.objects.get(id=booking_id, client_id=client_id)

        if booking.status == "cancelled":
            return JsonResponse({
                "success": False,
                "reason": "This booking is already cancelled."
            })

        booking.status = "cancelled"
        booking.save()

        return JsonResponse({
            "success": True,
            "message": f"Booking on {booking.date} at {booking.start_time} with {booking.staff.get_full_name()} has been cancelled.",
        })

    except SessionBooking.DoesNotExist:
        return JsonResponse({
            "success": False,
            "reason": "Booking not found or does not belong to this client."
        }, status=404)
    except ValueError as e:
        return JsonResponse({
            "success": False,
            "reason": f"Invalid format: {str(e)}"
        }, status=400)
