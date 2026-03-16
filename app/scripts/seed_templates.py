import asyncio

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import engine
from app.modules.templates.models import DialogTemplate

TEMPLATES = [
    {
        "name": "Make appointment",
        "base_script": (
            "Call the provided phone number and request an appointment. "
            "Introduce yourself as calling on behalf of the user. "
            "State the preferred date and time. "
            "If the preferred slot is unavailable, ask for the nearest available alternative. "
            "Confirm the final appointment details (date, time, location) before ending the call. "
            "Thank the interlocutor and end politely."
        ),
        "required_slots": [
            "preferred_date",
            "preferred_time",
            "service_type",
            "patient_name",
        ],
    },
    {
        "name": "Confirm reservation",
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
        "name": "Request information",
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
        "name": "Cancel appointment",
        "base_script": (
            "Call to cancel a previously scheduled appointment. "
            "Provide the appointment date, time, and the name it was booked under. "
            "If asked for a reason, provide the one given by the user. "
            "Ask if there are any cancellation fees or requirements. "
            "Confirm the cancellation and end the call."
        ),
        "required_slots": [
            "appointment_date",
            "appointment_time",
            "booked_name",
            "reason",
        ],
    },
    {
        "name": "Follow-up call",
        "base_script": (
            "Call to follow up on a previous interaction. "
            "Reference the previous contact using the reference number. "
            "Ask about the current status or any updates regarding the topic. "
            "If action is needed from the user's side, note what is required. "
            "Summarize any new information and end the call."
        ),
        "required_slots": ["reference_number", "contact_name", "follow_up_topic"],
    },
    {
        "name": "Reschedule appointment",
        "base_script": (
            "Call to reschedule an existing appointment. "
            "Provide the original appointment date, time, and the name it was booked under. "
            "Explain that you need to move it to the new preferred date and time. "
            "If the new slot is unavailable, ask for the closest alternative. "
            "Confirm the updated appointment details (new date, time, location) before ending. "
            "Ask if any preparation or documents are still required for the new date."
        ),
        "required_slots": [
            "original_date",
            "original_time",
            "new_preferred_date",
            "new_preferred_time",
            "booked_name",
            "service_type",
        ],
    },
    {
        "name": "Order status check",
        "base_script": (
            "Call to check the status of an order or delivery. "
            "Provide the order or tracking number and the customer name. "
            "Ask for the current status: is it processing, shipped, or delivered? "
            "If shipped, ask for the estimated delivery date and carrier details. "
            "If there are delays or issues, ask for the reason and expected resolution. "
            "Note all details and end the call politely."
        ),
        "required_slots": ["order_number", "customer_name"],
    },
    {
        "name": "File a complaint",
        "base_script": (
            "Call to file a complaint on behalf of the user. "
            "Introduce yourself and state that you are calling to report an issue. "
            "Clearly describe the problem using the details provided. "
            "Ask for a complaint reference number or ticket ID. "
            "Ask about the expected resolution timeline and next steps. "
            "Request confirmation that the complaint has been registered."
        ),
        "required_slots": ["complaint_subject", "complaint_details", "customer_name"],
    },
    {
        "name": "Prescription refill request",
        "base_script": (
            "Call the pharmacy to request a prescription refill. "
            "Provide the patient name and prescription number. "
            "Ask if the refill can be processed and when it will be ready for pickup. "
            "If the prescription has expired or needs doctor approval, ask what steps are needed. "
            "Confirm the pharmacy location and pickup hours. "
            "Thank the pharmacist and end the call."
        ),
        "required_slots": ["patient_name", "prescription_number", "pharmacy_name"],
    },
    {
        "name": "Service outage report",
        "base_script": (
            "Call the service provider to report an outage or service disruption. "
            "Provide the account number and describe the issue (internet, electricity, water, etc.). "
            "Ask if there is a known outage in the area. "
            "If not, request that a trouble ticket be opened and ask for the ticket number. "
            "Ask for the estimated time of restoration. "
            "Confirm the contact number for follow-up updates."
        ),
        "required_slots": [
            "account_number",
            "service_type",
            "issue_description",
            "customer_name",
        ],
    },
    {
        "name": "Insurance claim inquiry",
        "base_script": (
            "Call the insurance company to inquire about the status of a claim. "
            "Provide the claim number and the policyholder name. "
            "Ask for the current claim status: pending review, approved, or denied. "
            "If approved, ask about the payout amount and timeline. "
            "If denied or pending, ask what additional documents or actions are needed. "
            "Note all details and confirm the next steps."
        ),
        "required_slots": ["claim_number", "policyholder_name", "claim_type"],
    },
    {
        "name": "Payment reminder",
        "base_script": (
            "Call to remind about a pending payment or invoice. "
            "Introduce yourself as calling on behalf of the company. "
            "Reference the invoice number and the amount due. "
            "Politely ask if the payment has been made or when it is expected. "
            "If already paid, ask for the transaction reference for records. "
            "If not yet paid, confirm the payment methods available and the deadline. "
            "Thank them and end the call courteously."
        ),
        "required_slots": ["invoice_number", "amount_due", "due_date", "company_name"],
    },
]


async def seed() -> None:
    async with AsyncSession(engine) as session:
        for template_data in TEMPLATES:
            result = await session.exec(
                select(DialogTemplate).where(
                    DialogTemplate.name == template_data["name"]
                )
            )
            existing = result.first()
            if existing:
                print(
                    f"  SKIP: '{template_data['name']}' already exists (id={existing.id})"
                )
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
