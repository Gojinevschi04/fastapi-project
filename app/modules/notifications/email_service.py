from email.message import EmailMessage

import aiosmtplib

from app.core.config import settings
from app.core.logging import get_logger
from app.modules.notifications.constants import (
    BG,
    BOX_SHADOW,
    CARD_BG,
    DANGER,
    EMAIL_SUBJECT_PREFIX,
    FONT_STACK,
    GRAY,
    PRIMARY,
    STYLE_CENTER_BLOCK,
    STYLE_DANGER_BOX,
    STYLE_INFO_BOX,
    STYLE_NOTE,
    STYLE_PARAGRAPH,
    STYLE_SUCCESS_BOX,
    SUCCESS,
    WARNING,
)
from app.modules.notifications.translations import get_translations

logger = get_logger(__name__)


# ── HTML helpers ──


def _get_frontend_url() -> str:
    return settings.CORS_ORIGINS.split(",")[0] if settings.CORS_ORIGINS else settings.BASE_URL


def _base_template(title: str, accent: str, content: str) -> str:
    frontend_url = _get_frontend_url()
    card_style = f"background:{CARD_BG};border-radius:16px;overflow:hidden;{BOX_SHADOW}"
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width"></head>
<body style="margin:0;padding:0;background:{BG};font-family:{FONT_STACK};">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:{BG};padding:40px 20px;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="{card_style};">
        <tr><td style="background:linear-gradient(135deg,{PRIMARY},{accent});padding:32px 40px;">
          <h1 style="margin:0;color:#fff;font-size:22px;font-weight:700;">{title}</h1>
        </td></tr>
        <tr><td style="padding:32px 40px;">{content}</td></tr>
        <tr><td style="padding:20px 40px 28px;border-top:1px solid #f3f4f6;">
          <p style="margin:0;font-size:12px;color:{GRAY};">
            <a href="{frontend_url}" style="color:{PRIMARY};text-decoration:none;">Open Quiet Call AI</a>
            &nbsp;&middot;&nbsp; You received this email because you have an account with us.
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _paragraph(text: str) -> str:
    return f'<p style="{STYLE_PARAGRAPH}">{text}</p>'


def _note(text: str, extra_style: str = "") -> str:
    separator = ";" if extra_style else ""
    return f'<p style="{STYLE_NOTE}{separator}{extra_style}">{text}</p>'


def _button(text: str, url: str, color: str = PRIMARY) -> str:
    return (
        f'<a href="{url}" style="display:inline-block;padding:12px 28px;background:{color};'
        f'color:#fff;text-decoration:none;border-radius:10px;font-weight:600;font-size:14px;">'
        f"{text}</a>"
    )


def _centered_button(text: str, url: str, color: str = PRIMARY) -> str:
    return f'<div style="{STYLE_CENTER_BLOCK}">{_button(text, url, color)}</div>'


def _info_box(label: str, value: str) -> str:
    return (
        f'<div style="background:#f3f4f6;padding:14px 18px;border-radius:10px;margin:8px 0;">'
        f'<span style="font-size:12px;color:{GRAY};">{label}</span><br>'
        f'<span style="font-size:15px;font-weight:600;color:#111827;">{value}</span></div>'
    )


def _colored_box(label: str, value: str, box_style: str, label_color: str, value_color: str = "#374151") -> str:
    return (
        f'<div style="{box_style}">'
        f'<span style="font-size:12px;color:{label_color};font-weight:600;">{label}</span><br>'
        f'<span style="font-size:14px;color:{value_color};line-height:1.5;">{value}</span></div>'
    )


def _task_button(translations: dict[str, str], key: str, task_id: int | None, color: str) -> str:
    if not task_id:
        return ""
    task_url = f"{_get_frontend_url()}/tasks/{task_id}"
    return _centered_button(translations[key], task_url, color)


def _subject(title: str) -> str:
    return f"{EMAIL_SUBJECT_PREFIX} — {title}"


# ── Email service ──


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

    async def _send_translated(
        self, to_email: str, title_key: str, accent: str, content: str, language: str = "en"
    ) -> bool:
        translations = get_translations(language)
        title = translations[title_key]
        return await self.send_email(to_email, _subject(title), _base_template(title, accent, content))

    # ── Auth emails ──

    async def send_welcome(self, to_email: str, language: str = "en") -> bool:
        translations = get_translations(language)
        content = (
            _paragraph(translations["welcome_body"])
            + _paragraph(translations["welcome_body2"])
            + _centered_button(translations["go_to_dashboard"], _get_frontend_url())
        )
        return await self._send_translated(to_email, "welcome_title", PRIMARY, content, language)

    async def send_password_reset(self, to_email: str, reset_token: str, language: str = "en") -> bool:
        translations = get_translations(language)
        reset_url = f"{_get_frontend_url()}/reset-password?token={reset_token}"
        content = (
            _paragraph(translations["reset_body"])
            + _centered_button(translations["reset_button"], reset_url, WARNING)
            + _note(translations["reset_note"])
        )
        return await self._send_translated(to_email, "reset_title", WARNING, content, language)

    async def send_password_changed(self, to_email: str, language: str = "en") -> bool:
        translations = get_translations(language)
        content = (
            _paragraph(translations["password_changed_body"])
            + _paragraph(translations["password_changed_warning"])
        )
        return await self._send_translated(to_email, "password_changed_title", WARNING, content, language)

    async def send_email_changed(self, to_old_email: str, new_email: str, language: str = "en") -> bool:
        translations = get_translations(language)
        content = (
            _paragraph(f'{translations["email_changed_body"]} <strong>{new_email}</strong>.')
            + _paragraph(translations["email_changed_warning"])
        )
        return await self._send_translated(to_old_email, "email_changed_title", WARNING, content, language)

    # ── Task emails ──

    async def send_task_scheduled(
        self, to_email: str, task_phone: str, scheduled_time: str, language: str = "en"
    ) -> bool:
        translations = get_translations(language)
        content = (
            _paragraph(translations["scheduled_body"])
            + _info_box(translations["phone_number"], task_phone)
            + _info_box(translations["scheduled_for"], scheduled_time)
            + _note(translations["scheduled_followup"], extra_style="margin-top:16px")
        )
        return await self._send_translated(to_email, "call_scheduled", PRIMARY, content, language)

    async def send_task_success(
        self, to_email: str, task_phone: str, summary: str, task_id: int | None = None, language: str = "en"
    ) -> bool:
        translations = get_translations(language)
        content = (
            _paragraph(translations["call_completed_body"])
            + _info_box(translations["phone_number"], task_phone)
            + _colored_box(translations["ai_summary"], summary, STYLE_SUCCESS_BOX, SUCCESS)
            + _task_button(translations, "view_transcript", task_id, SUCCESS)
        )
        return await self._send_translated(to_email, "call_completed", SUCCESS, content, language)

    async def send_task_failure(
        self, to_email: str, task_phone: str, error_reason: str, task_id: int | None = None, language: str = "en"
    ) -> bool:
        translations = get_translations(language)
        content = (
            _paragraph(translations["call_failed_body"])
            + _info_box(translations["phone_number"], task_phone)
            + _colored_box(translations["reason"], error_reason, STYLE_DANGER_BOX, DANGER, "#991b1b")
            + _task_button(translations, "view_task_retry", task_id, DANGER)
        )
        return await self._send_translated(to_email, "call_failed", DANGER, content, language)

    # ── Feedback ──

    async def send_feedback(self, sender_name: str, sender_email: str, message: str) -> bool:
        recipients = [email.strip() for email in settings.FEEDBACK_EMAILS.split(",") if email.strip()]
        if not recipients:
            logger.warning("No FEEDBACK_EMAILS configured, skipping feedback delivery")
            return False

        content = (
            _paragraph("New feedback received from the contact form.")
            + _info_box("From", f"{sender_name} ({sender_email})")
            + _colored_box("Message", message, STYLE_INFO_BOX, GRAY)
            + _note(
                f'Reply directly to <a href="mailto:{sender_email}" style="color:{PRIMARY};">{sender_email}</a>'
            )
        )
        subject = _subject(f"Feedback from {sender_name}")
        body = _base_template("New Feedback", PRIMARY, content)

        all_sent = True
        for recipient in recipients:
            if not await self.send_email(recipient, subject, body):
                all_sent = False
        return all_sent
