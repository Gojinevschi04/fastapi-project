"""Seed demo data for testing/demo purposes.

Creates:
- 2 admin users + 8 regular users (10 total)
- 20+ tasks across all statuses
- Call sessions + transcript log lines for completed/failed tasks
"""

import asyncio
from datetime import datetime, timedelta

from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import engine
from app.modules.auth.service import AuthService
from app.modules.calls.models import CallSession, LogLine
from app.modules.calls.schema import Speaker
from app.modules.tasks.models import Task
from app.modules.tasks.schema import TaskStatus
from app.modules.templates.models import DialogTemplate
from app.modules.users.models import User
from app.modules.users.schema import UserRole

DEMO_USERS = [
    {"email": "admin@quietcall.ai", "role": UserRole.ADMIN, "password": "admin1234", "phone_number": "+37360000001"},
    {"email": "supervisor@quietcall.ai", "role": UserRole.ADMIN, "password": "admin1234", "phone_number": "+37360000010"},
    {"email": "ana@example.com", "role": UserRole.USER, "password": "password123", "phone_number": "+37360000002"},
    {"email": "john@example.com", "role": UserRole.USER, "password": "password123", "phone_number": "+37360000003"},
    {"email": "maria@example.com", "role": UserRole.USER, "password": "password123", "phone_number": "+37360000004"},
    {"email": "alex@example.com", "role": UserRole.USER, "password": "password123", "phone_number": "+37360000005"},
    {"email": "elena@example.com", "role": UserRole.USER, "password": "password123", "phone_number": "+37360000006"},
    {"email": "dmitri@example.com", "role": UserRole.USER, "password": "password123", "phone_number": "+37360000007"},
    {"email": "natalia@example.com", "role": UserRole.USER, "password": "password123", "phone_number": "+37360000008"},
    {"email": "victor@example.com", "role": UserRole.USER, "password": "password123", "phone_number": "+37360000009"},
]


async def seed_users(session: AsyncSession) -> dict[str, int]:
    """Returns dict of email → user_id."""
    user_ids: dict[str, int] = {}
    for ud in DEMO_USERS:
        result = await session.exec(select(User).where(User.email == ud["email"]))
        existing = result.first()
        if existing:
            print(f"  SKIP user: '{ud['email']}' (id={existing.id})")
            user_ids[ud["email"]] = existing.id
            continue
        user = User(
            email=ud["email"],
            role=ud["role"],
            hashed_password=AuthService.hash_password(ud["password"]),
            phone_number=ud["phone_number"],
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        print(f"  CREATED user: '{user.email}' (id={user.id}, role={user.role})")
        user_ids[ud["email"]] = user.id
    return user_ids


def _get_template_id(template_map: dict[str, DialogTemplate], name: str, fallback: DialogTemplate) -> int:
    return template_map.get(name, fallback).id


async def seed_tasks(session: AsyncSession, users: dict[str, int]) -> list[Task]:
    # Check existing task count
    result = await session.exec(select(func.count()).select_from(Task))
    count = result.one()
    if count >= 10:
        print(f"  SKIP tasks: {count} tasks already exist")
        return []

    result = await session.exec(select(DialogTemplate))
    templates = list(result.all())
    if not templates:
        print("  SKIP tasks: no templates — run 'make db.seed' first")
        return []

    # Build a name→id map (avoids lazy-loading issues)
    tm_ids: dict[str, int] = {t.name: t.id for t in templates}
    fb_id = templates[0].id
    now = datetime.now()

    tasks_data = [
        # --- Ana (heavy user) ---
        {"phone": "+37322123456", "status": TaskStatus.COMPLETED, "tpl": "Make Appointment", "user": "ana@example.com",
         "slots": {"preferred_date": "2026-03-20", "preferred_time": "10:00", "service_type": "dental", "patient_name": "Ana G."},
         "summary": "Appointment confirmed for March 20 at 10:00 AM at City Dental Clinic.", "ago_days": 8},
        {"phone": "+37322654321", "status": TaskStatus.COMPLETED, "tpl": "Confirm Reservation", "user": "ana@example.com",
         "slots": {"reservation_id": "RES-2026-0042", "reservation_date": "2026-03-18", "guest_name": "Ana Gojinevschi"},
         "summary": "Reservation confirmed for March 18, 2 guests, at La Placinte.", "ago_days": 6},
        {"phone": "+37322111222", "status": TaskStatus.FAILED, "tpl": "Make Appointment", "user": "ana@example.com",
         "slots": {"preferred_date": "2026-03-15", "preferred_time": "14:00", "service_type": "eye exam", "patient_name": "Ana G."},
         "error": "No available slots. Interlocutor suggested next week.", "ago_days": 4},
        {"phone": "+37322333444", "status": TaskStatus.PENDING, "tpl": "Request Information", "user": "ana@example.com",
         "slots": {"question_topic": "pricing for annual membership", "business_name": "FitLife Gym"}, "ago_hours": 6},
        {"phone": "+37322334455", "status": TaskStatus.COMPLETED, "tpl": "Follow-up Call", "user": "ana@example.com",
         "slots": {"reference_number": "ORD-88712", "contact_name": "DHL Support", "follow_up_topic": "parcel delivery status"},
         "summary": "Parcel out for delivery, expected by 5 PM today.", "ago_days": 2},
        # --- John ---
        {"phone": "+37322555666", "status": TaskStatus.COMPLETED, "tpl": "Cancel Appointment", "user": "john@example.com",
         "slots": {"appointment_date": "2026-03-12", "appointment_time": "09:00", "booked_name": "John Smith", "reason": "travel conflict"},
         "summary": "Appointment cancelled. No cancellation fee applied.", "ago_days": 7},
        {"phone": "+37322777888", "status": TaskStatus.COMPLETED, "tpl": "Follow-up Call", "user": "john@example.com",
         "slots": {"reference_number": "TKT-20260301", "contact_name": "Support Team", "follow_up_topic": "laptop repair"},
         "summary": "Repair completed. Pickup available Mon-Fri 9-17.", "ago_days": 3},
        {"phone": "+37322999000", "status": TaskStatus.SCHEDULED, "tpl": "Make Appointment", "user": "john@example.com",
         "slots": {"preferred_date": "2026-03-25", "preferred_time": "16:00", "service_type": "haircut", "patient_name": "John S."},
         "scheduled_future_days": 2, "ago_hours": 3},
        {"phone": "+37322999111", "status": TaskStatus.FAILED, "tpl": "Request Information", "user": "john@example.com",
         "slots": {"question_topic": "car service pricing", "business_name": "AutoPro Garage"},
         "error": "Line busy after 3 retries.", "ago_days": 1},
        # --- Maria ---
        {"phone": "+37322100200", "status": TaskStatus.COMPLETED, "tpl": "Confirm Reservation", "user": "maria@example.com",
         "slots": {"reservation_id": "HTL-5567", "reservation_date": "2026-04-01", "guest_name": "Maria P."},
         "summary": "Hotel reservation confirmed: April 1-3, double room, breakfast included.", "ago_days": 9},
        {"phone": "+37322300400", "status": TaskStatus.FAILED, "tpl": "Request Information", "user": "maria@example.com",
         "slots": {"question_topic": "opening hours", "business_name": "Central Post Office"},
         "error": "Cancelled by user", "ago_days": 2},
        {"phone": "+37322500600", "status": TaskStatus.COMPLETED, "tpl": "Make Appointment", "user": "maria@example.com",
         "slots": {"preferred_date": "2026-03-22", "preferred_time": "11:30", "service_type": "consultation", "patient_name": "Maria P."},
         "summary": "Consultation on March 22 at 11:30. Bring ID and insurance.", "ago_hours": 12},
        # --- Alex ---
        {"phone": "+37322600700", "status": TaskStatus.COMPLETED, "tpl": "Make Appointment", "user": "alex@example.com",
         "slots": {"preferred_date": "2026-03-19", "preferred_time": "09:30", "service_type": "visa interview", "patient_name": "Alex T."},
         "summary": "Interview confirmed at US Embassy, March 19, 09:30. Arrive 30 min early.", "ago_days": 5},
        {"phone": "+37322600800", "status": TaskStatus.PENDING, "tpl": "Cancel Appointment", "user": "alex@example.com",
         "slots": {"appointment_date": "2026-03-28", "appointment_time": "15:00", "booked_name": "Alex T.", "reason": "scheduling conflict"},
         "ago_hours": 2},
        # --- Elena ---
        {"phone": "+37322700900", "status": TaskStatus.COMPLETED, "tpl": "Follow-up Call", "user": "elena@example.com",
         "slots": {"reference_number": "CLM-4420", "contact_name": "Insurance Agent", "follow_up_topic": "claim status"},
         "summary": "Claim approved. Payment will be processed within 5 business days.", "ago_days": 3},
        {"phone": "+37322701000", "status": TaskStatus.IN_PROGRESS, "tpl": "Make Appointment", "user": "elena@example.com",
         "slots": {"preferred_date": "2026-03-26", "preferred_time": "14:00", "service_type": "notary", "patient_name": "Elena V."},
         "ago_hours": 0},
        # --- Dmitri ---
        {"phone": "+37322800100", "status": TaskStatus.COMPLETED, "tpl": "Confirm Reservation", "user": "dmitri@example.com",
         "slots": {"reservation_id": "FLT-MD-123", "reservation_date": "2026-04-05", "guest_name": "Dmitri K."},
         "summary": "Flight confirmed: April 5, Chisinau-Bucharest, 07:15, seat 12A.", "ago_days": 4},
        # --- Admin ---
        {"phone": "+37322700800", "status": TaskStatus.COMPLETED, "tpl": "Follow-up Call", "user": "admin@quietcall.ai",
         "slots": {"reference_number": "INC-001", "contact_name": "Twilio Support", "follow_up_topic": "API rate limits"},
         "summary": "Twilio confirmed: 100 concurrent calls on current plan. Upgrade available.", "ago_days": 10},
        {"phone": "+37322800900", "status": TaskStatus.PENDING, "tpl": "Request Information", "user": "admin@quietcall.ai",
         "slots": {"question_topic": "enterprise pricing", "business_name": "OpenAI"}, "ago_hours": 1},
        {"phone": "+37322801000", "status": TaskStatus.COMPLETED, "tpl": "Make Appointment", "user": "admin@quietcall.ai",
         "slots": {"preferred_date": "2026-03-14", "preferred_time": "10:00", "service_type": "demo meeting", "patient_name": "Admin"},
         "summary": "Demo meeting scheduled with client at HQ, March 14 at 10 AM.", "ago_days": 6},
    ]

    created_task_ids: list[tuple[int, str]] = []  # (task_id, status)
    for td in tasks_data:
        task = Task(
            target_phone=td["phone"],
            status=td["status"],
            template_id=tm_ids.get(td["tpl"], fb_id),
            user_id=users[td["user"]],
            slot_data=td["slots"],
            scheduled_time=now + timedelta(days=td["scheduled_future_days"]) if "scheduled_future_days" in td else None,
            summary=td.get("summary"),
            error_reason=td.get("error"),
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        created_task_ids.append((task.id, td["status"]))

    print(f"  CREATED {len(created_task_ids)} demo tasks")
    return created_task_ids


TRANSCRIPTS: dict[str, list[dict]] = {
    "appointment_success": [
        {"speaker": Speaker.AGENT, "text": "Hello, I'm calling on behalf of a patient to schedule an appointment.", "intent": None},
        {"speaker": Speaker.INTERLOCUTOR, "text": "Sure, what date were you looking at?", "intent": "request_info"},
        {"speaker": Speaker.AGENT, "text": "We'd prefer March 20 at 10:00 AM if possible.", "intent": None},
        {"speaker": Speaker.INTERLOCUTOR, "text": "Let me check... Yes, that slot is available.", "intent": "confirmation"},
        {"speaker": Speaker.AGENT, "text": "Perfect. Can you confirm the address and any preparation needed?", "intent": None},
        {"speaker": Speaker.INTERLOCUTOR, "text": "City Dental Clinic, 45 Stefan cel Mare. No special preparation needed.", "intent": "provide_info"},
        {"speaker": Speaker.AGENT, "text": "Thank you very much. The appointment is confirmed for March 20 at 10 AM. Have a great day! [OBJECTIVE_ACHIEVED]", "intent": None},
        {"speaker": Speaker.INTERLOCUTOR, "text": "You too, goodbye!", "intent": "farewell"},
    ],
    "reservation_confirmed": [
        {"speaker": Speaker.AGENT, "text": "Hello, I'm calling to confirm reservation RES-2026-0042 for March 18.", "intent": None},
        {"speaker": Speaker.INTERLOCUTOR, "text": "One moment please... Yes, I see it. Table for 2 at 7 PM.", "intent": "confirmation"},
        {"speaker": Speaker.AGENT, "text": "That's correct. Is everything still on track?", "intent": None},
        {"speaker": Speaker.INTERLOCUTOR, "text": "Yes, all confirmed. See you then!", "intent": "confirmation"},
        {"speaker": Speaker.AGENT, "text": "Wonderful, thank you. Goodbye! [OBJECTIVE_ACHIEVED]", "intent": None},
    ],
    "appointment_failed": [
        {"speaker": Speaker.AGENT, "text": "Hello, I'd like to book an eye exam for March 15 at 2 PM.", "intent": None},
        {"speaker": Speaker.INTERLOCUTOR, "text": "I'm sorry, we're fully booked on the 15th.", "intent": "rejection"},
        {"speaker": Speaker.AGENT, "text": "Is there anything available that week?", "intent": None},
        {"speaker": Speaker.INTERLOCUTOR, "text": "The earliest opening is March 22 at 3 PM.", "intent": "provide_info"},
        {"speaker": Speaker.AGENT, "text": "I'll need to check with the patient. Thank you for the information. [OBJECTIVE_FAILED]", "intent": None},
    ],
    "follow_up_success": [
        {"speaker": Speaker.AGENT, "text": "Hi, I'm calling about reference number ORD-88712 regarding a parcel delivery.", "intent": None},
        {"speaker": Speaker.INTERLOCUTOR, "text": "Let me pull that up... Yes, the parcel is currently out for delivery.", "intent": "provide_info"},
        {"speaker": Speaker.AGENT, "text": "When can we expect it to arrive?", "intent": None},
        {"speaker": Speaker.INTERLOCUTOR, "text": "It should be delivered by 5 PM today.", "intent": "provide_info"},
        {"speaker": Speaker.AGENT, "text": "Great, thank you for the update! [OBJECTIVE_ACHIEVED]", "intent": None},
    ],
    "cancellation_success": [
        {"speaker": Speaker.AGENT, "text": "Hello, I need to cancel an appointment on March 12 at 9 AM for John Smith.", "intent": None},
        {"speaker": Speaker.INTERLOCUTOR, "text": "I see the appointment. May I ask the reason for cancellation?", "intent": "request_info"},
        {"speaker": Speaker.AGENT, "text": "There's a travel conflict. Is there a cancellation fee?", "intent": None},
        {"speaker": Speaker.INTERLOCUTOR, "text": "No fee for cancellations more than 24 hours in advance. It's cancelled.", "intent": "confirmation"},
        {"speaker": Speaker.AGENT, "text": "Thank you very much. Have a good day! [OBJECTIVE_ACHIEVED]", "intent": None},
    ],
}


async def seed_call_sessions(session: AsyncSession, tasks: list[tuple[int, str]]) -> None:
    # Check if sessions already exist
    result = await session.exec(select(func.count()).select_from(CallSession))
    count = result.one()
    if count > 0:
        print(f"  SKIP call sessions: {count} already exist")
        return

    transcript_keys = list(TRANSCRIPTS.keys())
    t_idx = 0
    created_sessions = 0
    created_lines = 0

    # Get all completed/failed tasks from DB
    result = await session.exec(
        select(Task.id, Task.status).where(Task.status.in_([TaskStatus.COMPLETED, TaskStatus.FAILED]))
    )
    eligible_tasks = result.all()

    for task_id, task_status in eligible_tasks:

        now = datetime.now()
        duration = 45 + (task_id * 7) % 120

        cs = CallSession(
            task_id=task_id,
            start_time=now - timedelta(days=task_id % 10, hours=task_id % 5),
            duration=duration,
            recording_uri=f"https://api.twilio.com/2010-04-01/Accounts/DEMO/Recordings/RE{task_id:06d}.wav",
        )
        session.add(cs)
        await session.commit()
        await session.refresh(cs)
        created_sessions += 1

        # Pick a transcript template
        key = transcript_keys[t_idx % len(transcript_keys)]
        t_idx += 1
        transcript = TRANSCRIPTS[key]

        base_time = cs.start_time
        for i, line in enumerate(transcript):
            log = LogLine(
                session_id=cs.id,
                timestamp=base_time + timedelta(seconds=i * 8),
                speaker=line["speaker"],
                text=line["text"],
                detected_intent=line["intent"],
            )
            session.add(log)
            created_lines += 1

        await session.commit()

    print(f"  CREATED {created_sessions} call sessions with {created_lines} log lines")


async def seed() -> None:
    async with AsyncSession(engine) as session:
        print("\n--- Seeding demo users ---")
        users = await seed_users(session)

        print("\n--- Seeding demo tasks ---")
        tasks = await seed_tasks(session, users)

        print("\n--- Seeding call sessions & transcripts ---")
        await seed_call_sessions(session, tasks)

    print("\nDemo seed completed.")
    print("\nDemo accounts:")
    print("  Admin:      admin@quietcall.ai / admin1234")
    print("  Supervisor: supervisor@quietcall.ai / admin1234")
    print("  Users:      ana@example.com / password123")
    print("              john@example.com / password123")
    print("              maria@example.com / password123")
    print("              alex@example.com / password123")
    print("              elena@example.com / password123")
    print("              dmitri@example.com / password123")
    print("              natalia@example.com / password123")
    print("              victor@example.com / password123")


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
