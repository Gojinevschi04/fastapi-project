"""Seed demo users and tasks for testing/demo purposes.

Creates:
- 1 admin user (admin@quietcall.ai / admin123)
- 3 regular users
- 10-15 tasks across different statuses and templates
"""

import asyncio
from datetime import datetime, timedelta

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import engine
from app.modules.auth.service import AuthService
from app.modules.tasks.models import Task
from app.modules.tasks.schema import TaskStatus
from app.modules.templates.models import DialogTemplate
from app.modules.users.models import User
from app.modules.users.schema import UserRole

DEMO_USERS = [
    {
        "email": "admin@quietcall.ai",
        "role": UserRole.ADMIN,
        "password": "admin123",
        "phone_number": "+37360000001",
    },
    {
        "email": "ana@example.com",
        "role": UserRole.USER,
        "password": "password123",
        "phone_number": "+37360000002",
    },
    {
        "email": "john@example.com",
        "role": UserRole.USER,
        "password": "password123",
        "phone_number": "+37360000003",
    },
    {
        "email": "maria@example.com",
        "role": UserRole.USER,
        "password": "password123",
        "phone_number": "+37360000004",
    },
]


async def seed_users(session: AsyncSession) -> dict[str, User]:
    users: dict[str, User] = {}

    for user_data in DEMO_USERS:
        result = await session.exec(select(User).where(User.email == user_data["email"]))
        existing = result.first()
        if existing:
            print(f"  SKIP user: '{user_data['email']}' already exists (id={existing.id})")
            users[user_data["email"]] = existing
            continue

        user = User(
            email=user_data["email"],
            role=user_data["role"],
            hashed_password=AuthService.hash_password(user_data["password"]),
            phone_number=user_data["phone_number"],
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        print(f"  CREATED user: '{user.email}' (id={user.id}, role={user.role})")
        users[user_data["email"]] = user

    return users


async def seed_tasks(session: AsyncSession, users: dict[str, User]) -> None:
    # Check if tasks already exist
    result = await session.exec(select(Task).limit(1))
    if result.first():
        print("  SKIP tasks: tasks already exist in database")
        return

    # Get templates
    result = await session.exec(select(DialogTemplate))
    templates = result.all()
    if not templates:
        print("  SKIP tasks: no templates found — run 'make db.seed' first")
        return

    template_map = {t.name: t for t in templates}
    now = datetime.now()

    demo_tasks = [
        # Ana's tasks
        {
            "target_phone": "+37322123456",
            "status": TaskStatus.COMPLETED,
            "template_id": template_map.get("Make Appointment", templates[0]).id,
            "user_id": users["ana@example.com"].id,
            "slot_data": {"preferred_date": "2026-03-20", "preferred_time": "10:00", "service_type": "dental", "patient_name": "Ana G."},
            "summary": "Appointment confirmed for March 20 at 10:00 AM at City Dental Clinic.",
            "created_at": now - timedelta(days=5),
        },
        {
            "target_phone": "+37322654321",
            "status": TaskStatus.COMPLETED,
            "template_id": template_map.get("Confirm Reservation", templates[0]).id,
            "user_id": users["ana@example.com"].id,
            "slot_data": {"reservation_id": "RES-2026-0042", "reservation_date": "2026-03-18", "guest_name": "Ana Gojinevschi"},
            "summary": "Reservation confirmed for March 18, 2 guests, at La Placinte restaurant.",
            "created_at": now - timedelta(days=3),
        },
        {
            "target_phone": "+37322111222",
            "status": TaskStatus.FAILED,
            "template_id": template_map.get("Make Appointment", templates[0]).id,
            "user_id": users["ana@example.com"].id,
            "slot_data": {"preferred_date": "2026-03-15", "preferred_time": "14:00", "service_type": "eye exam", "patient_name": "Ana G."},
            "error_reason": "No available slots for the requested date. Interlocutor suggested next week.",
            "created_at": now - timedelta(days=2),
        },
        {
            "target_phone": "+37322333444",
            "status": TaskStatus.PENDING,
            "template_id": template_map.get("Request Information", templates[0]).id,
            "user_id": users["ana@example.com"].id,
            "slot_data": {"question_topic": "pricing for annual membership", "business_name": "FitLife Gym"},
            "created_at": now - timedelta(hours=6),
        },
        # John's tasks
        {
            "target_phone": "+37322555666",
            "status": TaskStatus.COMPLETED,
            "template_id": template_map.get("Cancel Appointment", templates[0]).id,
            "user_id": users["john@example.com"].id,
            "slot_data": {"appointment_date": "2026-03-12", "appointment_time": "09:00", "booked_name": "John Smith", "reason": "travel conflict"},
            "summary": "Appointment cancelled successfully. No cancellation fee applied.",
            "created_at": now - timedelta(days=4),
        },
        {
            "target_phone": "+37322777888",
            "status": TaskStatus.COMPLETED,
            "template_id": template_map.get("Follow-up Call", templates[0]).id,
            "user_id": users["john@example.com"].id,
            "slot_data": {"reference_number": "TKT-20260301", "contact_name": "Support Team", "follow_up_topic": "laptop repair status"},
            "summary": "Repair completed. Pickup available at service center, Monday-Friday 9-17.",
            "created_at": now - timedelta(days=1),
        },
        {
            "target_phone": "+37322999000",
            "status": TaskStatus.SCHEDULED,
            "template_id": template_map.get("Make Appointment", templates[0]).id,
            "user_id": users["john@example.com"].id,
            "slot_data": {"preferred_date": "2026-03-25", "preferred_time": "16:00", "service_type": "haircut", "patient_name": "John S."},
            "scheduled_time": now + timedelta(days=2),
            "created_at": now - timedelta(hours=3),
        },
        # Maria's tasks
        {
            "target_phone": "+37322100200",
            "status": TaskStatus.COMPLETED,
            "template_id": template_map.get("Confirm Reservation", templates[0]).id,
            "user_id": users["maria@example.com"].id,
            "slot_data": {"reservation_id": "HTL-5567", "reservation_date": "2026-04-01", "guest_name": "Maria P."},
            "summary": "Hotel reservation confirmed: April 1-3, double room, breakfast included.",
            "created_at": now - timedelta(days=6),
        },
        {
            "target_phone": "+37322300400",
            "status": TaskStatus.FAILED,
            "template_id": template_map.get("Request Information", templates[0]).id,
            "user_id": users["maria@example.com"].id,
            "slot_data": {"question_topic": "opening hours", "business_name": "Central Post Office"},
            "error_reason": "Cancelled by user",
            "created_at": now - timedelta(days=1),
        },
        {
            "target_phone": "+37322500600",
            "status": TaskStatus.COMPLETED,
            "template_id": template_map.get("Make Appointment", templates[0]).id,
            "user_id": users["maria@example.com"].id,
            "slot_data": {"preferred_date": "2026-03-22", "preferred_time": "11:30", "service_type": "consultation", "patient_name": "Maria P."},
            "summary": "Consultation scheduled for March 22 at 11:30. Bring ID and insurance card.",
            "created_at": now - timedelta(hours=12),
        },
        # Admin tasks
        {
            "target_phone": "+37322700800",
            "status": TaskStatus.COMPLETED,
            "template_id": template_map.get("Follow-up Call", templates[0]).id,
            "user_id": users["admin@quietcall.ai"].id,
            "slot_data": {"reference_number": "INC-001", "contact_name": "Twilio Support", "follow_up_topic": "API rate limits"},
            "summary": "Twilio confirmed: current plan allows 100 concurrent calls. Upgrade available.",
            "created_at": now - timedelta(days=7),
        },
        {
            "target_phone": "+37322800900",
            "status": TaskStatus.PENDING,
            "template_id": template_map.get("Request Information", templates[0]).id,
            "user_id": users["admin@quietcall.ai"].id,
            "slot_data": {"question_topic": "enterprise pricing", "business_name": "OpenAI"},
            "created_at": now - timedelta(hours=1),
        },
    ]

    for task_data in demo_tasks:
        task = Task(
            target_phone=task_data["target_phone"],
            status=task_data["status"],
            template_id=task_data["template_id"],
            user_id=task_data["user_id"],
            slot_data=task_data["slot_data"],
            scheduled_time=task_data.get("scheduled_time"),
            summary=task_data.get("summary"),
            error_reason=task_data.get("error_reason"),
        )
        session.add(task)

    await session.commit()
    print(f"  CREATED {len(demo_tasks)} demo tasks")


async def seed() -> None:
    async with AsyncSession(engine) as session:
        print("\n--- Seeding demo users ---")
        users = await seed_users(session)

        print("\n--- Seeding demo tasks ---")
        await seed_tasks(session, users)

    print("\nDemo seed completed.")
    print("\nDemo accounts:")
    print("  Admin: admin@quietcall.ai / admin123")
    print("  User:  ana@example.com / password123")
    print("  User:  john@example.com / password123")
    print("  User:  maria@example.com / password123")


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
