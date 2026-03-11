from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_send_email_disabled() -> None:
    with patch("app.modules.notifications.email_service.settings") as mock_settings:
        mock_settings.EMAIL_ENABLED = False

        from app.modules.notifications.email_service import EmailService

        service = EmailService()
        result = await service.send_email("user@example.com", "Test", "<p>Hello</p>")

        assert result is True


@pytest.mark.asyncio
async def test_send_email_enabled_success() -> None:
    with patch("app.modules.notifications.email_service.settings") as mock_settings, \
         patch("app.modules.notifications.email_service.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        mock_settings.EMAIL_ENABLED = True
        mock_settings.EMAIL_FROM = "noreply@test.com"
        mock_settings.EMAIL_FROM_NAME = "Test"
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = "user"
        mock_settings.SMTP_PASSWORD = "pass"

        from app.modules.notifications.email_service import EmailService

        service = EmailService()
        result = await service.send_email("user@example.com", "Test", "<p>Hello</p>")

        assert result is True
        mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_send_email_failure() -> None:
    with patch("app.modules.notifications.email_service.settings") as mock_settings, \
         patch("app.modules.notifications.email_service.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        mock_settings.EMAIL_ENABLED = True
        mock_settings.EMAIL_FROM = "noreply@test.com"
        mock_settings.EMAIL_FROM_NAME = "Test"
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = "user"
        mock_settings.SMTP_PASSWORD = "pass"
        mock_send.side_effect = Exception("SMTP connection failed")

        from app.modules.notifications.email_service import EmailService

        service = EmailService()
        result = await service.send_email("user@example.com", "Test", "<p>Hello</p>")

        assert result is False


@pytest.mark.asyncio
async def test_send_task_success_email() -> None:
    with patch("app.modules.notifications.email_service.settings") as mock_settings:
        mock_settings.EMAIL_ENABLED = False
        mock_settings.BASE_URL = "http://localhost:8000"

        from app.modules.notifications.email_service import EmailService

        service = EmailService()
        result = await service.send_task_success(
            to_email="user@example.com",
            task_phone="+37312345678",
            summary="Appointment confirmed for March 20.",
        )

        assert result is True


@pytest.mark.asyncio
async def test_send_task_failure_email() -> None:
    with patch("app.modules.notifications.email_service.settings") as mock_settings:
        mock_settings.EMAIL_ENABLED = False
        mock_settings.BASE_URL = "http://localhost:8000"

        from app.modules.notifications.email_service import EmailService

        service = EmailService()
        result = await service.send_task_failure(
            to_email="user@example.com",
            task_phone="+37312345678",
            error_reason="No answer after 3 retries.",
        )

        assert result is True
