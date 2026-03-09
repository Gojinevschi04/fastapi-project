from email.message import EmailMessage

import aiosmtplib

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmailService:
    async def send_email(self, to_email: str, subject: str, body_html: str) -> bool:
        if not settings.EMAIL_ENABLED:
            logger.info("Email disabled — would send to %s: %s", to_email, subject)
            return True

        message = EmailMessage()
        message["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body_html, subtype="html")

        try:
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                start_tls=True,
            )
            logger.info("Email sent to %s: %s", to_email, subject)
            return True
        except Exception:
            logger.exception("Failed to send email to %s", to_email)
            return False

    async def send_task_success(self, to_email: str, task_phone: str, summary: str) -> bool:
        subject = "Quiet Call AI — Call Completed Successfully"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #22c55e;">Call Completed Successfully</h2>
            <p>Your automated call to <strong>{task_phone}</strong> has been completed.</p>
            <h3>Summary</h3>
            <p style="background: #f3f4f6; padding: 12px; border-radius: 8px;">{summary}</p>
            <p style="color: #6b7280; font-size: 12px;">
                View full details in your <a href="{settings.BASE_URL}">Quiet Call AI dashboard</a>.
            </p>
        </body>
        </html>
        """
        return await self.send_email(to_email, subject, body)

    async def send_task_failure(self, to_email: str, task_phone: str, error_reason: str) -> bool:
        subject = "Quiet Call AI — Call Failed"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #ef4444;">Call Failed</h2>
            <p>Your automated call to <strong>{task_phone}</strong> could not be completed.</p>
            <h3>Reason</h3>
            <p style="background: #fef2f2; padding: 12px; border-radius: 8px; color: #991b1b;">{error_reason}</p>
            <p style="color: #6b7280; font-size: 12px;">
                You can retry from your <a href="{settings.BASE_URL}">Quiet Call AI dashboard</a>.
            </p>
        </body>
        </html>
        """
        return await self.send_email(to_email, subject, body)
