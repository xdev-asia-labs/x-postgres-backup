"""Notification service - handles Telegram and Email notifications."""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Literal

import aiosmtplib
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def send_telegram_notification(message: str) -> bool:
    """Send a notification via Telegram."""
    if not settings.TELEGRAM_ENABLED:
        return False

    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        logger.warning("Telegram is enabled but bot token or chat ID is missing")
        return False

    try:
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                json={
                    "chat_id": settings.TELEGRAM_CHAT_ID,
                    "text": message,
                    "parse_mode": "HTML",
                },
            )
            response.raise_for_status()
            logger.info("Telegram notification sent successfully")
            return True
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {e}")
        return False


async def send_email_notification(subject: str, body: str, html: bool = False) -> bool:
    """Send a notification via Email."""
    if not settings.EMAIL_ENABLED:
        return False

    if not settings.EMAIL_SMTP_USER or not settings.EMAIL_FROM or not settings.EMAIL_TO:
        logger.warning("Email is enabled but SMTP credentials or recipients are missing")
        return False

    try:
        message = MIMEMultipart("alternative")
        message["From"] = settings.EMAIL_FROM
        message["To"] = ", ".join(settings.EMAIL_TO)
        message["Subject"] = subject

        if html:
            message.attach(MIMEText(body, "html"))
        else:
            message.attach(MIMEText(body, "plain"))

        smtp_params = {
            "hostname": settings.EMAIL_SMTP_HOST,
            "port": settings.EMAIL_SMTP_PORT,
            "username": settings.EMAIL_SMTP_USER,
            "password": settings.EMAIL_SMTP_PASSWORD,
            "use_tls": settings.EMAIL_USE_TLS,
        }

        await aiosmtplib.send(message, **smtp_params)
        logger.info(f"Email notification sent successfully to {len(settings.EMAIL_TO)} recipients")
        return True
    except Exception as e:
        logger.error(f"Failed to send email notification: {e}")
        return False


async def notify_backup_status(
    backup_type: str,
    status: Literal["success", "failed"],
    database_name: str | None = None,
    source_host: str | None = None,
    size: str | None = None,
    duration: float | None = None,
    error: str | None = None,
) -> None:
    """Send notification about backup status."""
    emoji = "✅" if status == "success" else "❌"
    status_text = "THÀNH CÔNG" if status == "success" else "THẤT BẠI"

    # Prepare Telegram message
    telegram_msg = f"{emoji} <b>Backup {status_text}</b>\n\n"
    telegram_msg += f"📦 Loại: <code>{backup_type}</code>\n"
    if database_name:
        telegram_msg += f"🗄️ Database: <code>{database_name}</code>\n"
    if source_host:
        telegram_msg += f"🖥️ Server: <code>{source_host}</code>\n"
    if size:
        telegram_msg += f"💾 Dung lượng: {size}\n"
    if duration:
        telegram_msg += f"⏱️ Thời gian: {duration:.1f}s\n"
    if error:
        telegram_msg += f"\n⚠️ Lỗi: <code>{error[:500]}</code>\n"

    # Prepare Email message
    email_subject = f"[{settings.APP_NAME}] Backup {status_text} - {backup_type}"
    email_body = f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <h2 style="color: {'green' if status == 'success' else 'red'};">
        {emoji} Backup {status_text}
    </h2>
    <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Loại Backup:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{backup_type}</td>
        </tr>
"""
    if database_name:
        email_body += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Database:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{database_name}</td>
        </tr>
"""
    if source_host:
        email_body += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Server:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{source_host}</td>
        </tr>
"""
    if size:
        email_body += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Dung lượng:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{size}</td>
        </tr>
"""
    if duration:
        email_body += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Thời gian:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{duration:.1f}s</td>
        </tr>
"""
    if error:
        email_body += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Lỗi:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd; color: red;">{error[:500]}</td>
        </tr>
"""
    email_body += """
    </table>
</body>
</html>
"""

    # Send notifications
    await send_telegram_notification(telegram_msg)
    await send_email_notification(email_subject, email_body, html=True)


async def notify_restore_status(
    status: Literal["success", "failed"],
    database_name: str,
    target_host: str | None = None,
    file_path: str | None = None,
    duration: float | None = None,
    error: str | None = None,
) -> None:
    """Send notification about restore status."""
    emoji = "✅" if status == "success" else "❌"
    status_text = "THÀNH CÔNG" if status == "success" else "THẤT BẠI"

    # Prepare Telegram message
    telegram_msg = f"{emoji} <b>Restore {status_text}</b>\n\n"
    telegram_msg += f"🗄️ Database: <code>{database_name}</code>\n"
    if target_host:
        telegram_msg += f"🖥️ Server: <code>{target_host}</code>\n"
    if file_path:
        telegram_msg += f"📁 File: <code>{file_path}</code>\n"
    if duration:
        telegram_msg += f"⏱️ Thời gian: {duration:.1f}s\n"
    if error:
        telegram_msg += f"\n⚠️ Lỗi: <code>{error[:500]}</code>\n"

    # Prepare Email message
    email_subject = f"[{settings.APP_NAME}] Restore {status_text} - {database_name}"
    email_body = f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <h2 style="color: {'green' if status == 'success' else 'red'};">
        {emoji} Restore {status_text}
    </h2>
    <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Database:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{database_name}</td>
        </tr>
"""
    if target_host:
        email_body += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Server:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{target_host}</td>
        </tr>
"""
    if file_path:
        email_body += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>File:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{file_path}</td>
        </tr>
"""
    if duration:
        email_body += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Thời gian:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{duration:.1f}s</td>
        </tr>
"""
    if error:
        email_body += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Lỗi:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd; color: red;">{error[:500]}</td>
        </tr>
"""
    email_body += """
    </table>
</body>
</html>
"""

    # Send notifications
    await send_telegram_notification(telegram_msg)
    await send_email_notification(email_subject, email_body, html=True)
