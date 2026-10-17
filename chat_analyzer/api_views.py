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

        # ── LAYER 3: Slot conflict ──
        # Is there already a booking at this date+time with this staff?
        # Allow 1-hour slots: check if any booking overlaps within the same hour
        booking_exists = SessionBooking.objects.filter(
            staff=staff,
            date=target_date,
            start_time__lte=target_time,
            end_time__gt=target_time,
            status__in=["pending", "confirmed"],
        ).exists()

        if booking_exists:
            return JsonResponse({
                "available": False,
                "reason": f"Slot {time_str} on {date_str} is already booked with {staff.get_full_name()}.",
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
        # Layer 1
        try:
            schedule = StaffSchedule.objects.get(staff=staff, day_of_week=weekday)
        except StaffSchedule.DoesNotExist:
            return JsonResponse({
                "success": False,
                "reason": f"{staff.get_full_name()} does not work on {target_date.strftime('%A')}."
            })

        if not schedule.is_available or not (schedule.start_time <= target_time <= schedule.end_time):
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

        # Layer 3 — slot conflict
        if SessionBooking.objects.filter(
            staff=staff, date=target_date,
            start_time__lte=target_time, end_time__gt=target_time,
            status__in=["pending", "confirmed"],
        ).exists():
            return JsonResponse({
                "success": False,
                "reason": f"Slot {time_str} on {date_str} is already booked."
            })

        # ✅ Create the booking (default 1-hour session)
        end_time = (datetime.combine(date.today(), target_time) + timedelta(hours=1)).time()
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
