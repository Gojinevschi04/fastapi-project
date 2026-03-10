import asyncio

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import engine
from app.modules.templates.models import DialogTemplate

TEMPLATES = [
    {
        "name": "Make Appointment",
        "base_script": (
            "Call the provided phone number and request an appointment. "
            "Introduce yourself as calling on behalf of the user. "
            "State the preferred date and time. "
            "If the preferred slot is unavailable, ask for the nearest available alternative. "
            "Confirm the final appointment details (date, time, location) before ending the call. "
            "Thank the interlocutor and end politely."
        ),
        "required_slots": ["preferred_date", "preferred_time", "service_type", "patient_name"],
    },
    {
        "name": "Confirm Reservation",
        "base_script": (
            "Call to confirm an existing reservation. "
            "Provide the reservation ID and guest name. "
            "Ask the interlocutor to confirm that the reservation is still active for the given date. "
            "If there are any changes (time, number of guests), note them. "
            "Confirm the final details and end the call."
        ),
        "required_slots": ["reservation_id", "reservation_date", "guest_name"],
    },
    {
        "name": "Request Information",
        "base_script": (
            "Call the business and ask about the specified topic. "
            "Be specific about what information is needed. "
            "Ask about business hours, pricing, or available services as relevant. "
            "Take note of all details provided. "
            "Thank them for the information and end politely."
        ),
        "required_slots": ["question_topic", "business_name"],
    },
    {
        "name": "Cancel Appointment",
        "base_script": (
            "Call to cancel a previously scheduled appointment. "
            "Provide the appointment date, time, and the name it was booked under. "
            "If asked for a reason, provide the one given by the user. "
            "Ask if there are any cancellation fees or requirements. "
            "Confirm the cancellation and end the call."
        ),
        "required_slots": ["appointment_date", "appointment_time", "booked_name", "reason"],
    },
    {
        "name": "Follow-up Call",
        "base_script": (
            "Call to follow up on a previous interaction. "
            "Reference the previous contact using the reference number. "
            "Ask about the current status or any updates regarding the topic. "
            "If action is needed from the user's side, note what is required. "
            "Summarize any new information and end the call."
        ),
        "required_slots": ["reference_number", "contact_name", "follow_up_topic"],
    },
]


async def seed() -> None:
    async with AsyncSession(engine) as session:
        for template_data in TEMPLATES:
            result = await session.exec(
                select(DialogTemplate).where(DialogTemplate.name == template_data["name"])
            )
            existing = result.first()
            if existing:
                print(f"  SKIP: '{template_data['name']}' already exists (id={existing.id})")
                continue

            template = DialogTemplate(**template_data)
            session.add(template)
            await session.commit()
            await session.refresh(template)
            print(f"  CREATED: '{template.name}' (id={template.id})")

    print("\nSeed completed.")


def main() -> None:
    print("Seeding dialog templates...")
    asyncio.run(seed())


if __name__ == "__main__":
    main()
