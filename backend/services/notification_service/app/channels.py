import asyncio
import smtplib
from email.message import EmailMessage
from typing import Protocol

import httpx
from mip_common.config import get_settings

from .schemas import NotificationSendRequest


class NotificationChannelSender(Protocol):
    async def send(self, request: NotificationSendRequest) -> None:
        ...


class ConsoleSender:
    async def send(self, request: NotificationSendRequest) -> None:
        print(f"[{request.message.severity}] {request.message.title}: {request.message.body}")


class WebhookSender:
    async def send(self, request: NotificationSendRequest) -> None:
        target = request.target or get_settings().notification_webhook_url
        if not target:
            raise ValueError("Webhook target is not configured")
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                target,
                json={
                    "title": request.message.title,
                    "text": request.message.body,
                    "severity": request.message.severity,
                    "metadata": request.message.metadata,
                },
            )
            response.raise_for_status()


class TelegramSender:
    async def send(self, request: NotificationSendRequest) -> None:
        settings = get_settings()
        token = settings.telegram_bot_token
        chat_id = request.target or settings.telegram_chat_id
        if not token or not chat_id:
            raise ValueError("Telegram token or chat id is not configured")
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": f"{request.message.title}\n\n{request.message.body}",
                },
            )
            response.raise_for_status()


class EmailSender:
    async def send(self, request: NotificationSendRequest) -> None:
        await asyncio.to_thread(self._send_sync, request)

    def _send_sync(self, request: NotificationSendRequest) -> None:
        settings = get_settings()
        target = request.target
        if not settings.smtp_host or not target:
            raise ValueError("SMTP host or email target is not configured")
        message = EmailMessage()
        message["Subject"] = request.message.title
        message["From"] = settings.notification_email_from or settings.smtp_user
        message["To"] = target
        message.set_content(request.message.body)
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            smtp.starttls()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(message)


def create_sender(channel: str) -> NotificationChannelSender:
    if channel == "console":
        return ConsoleSender()
    if channel == "webhook":
        return WebhookSender()
    if channel == "telegram":
        return TelegramSender()
    if channel == "email":
        return EmailSender()
    raise ValueError("Unsupported notification channel")
