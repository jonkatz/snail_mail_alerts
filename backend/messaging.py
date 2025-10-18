from typing import Optional
import os
from twilio.rest import Client
from analyze_mail import MailAnalysis
from config import Config


def format_mail_summary(
    analysis: MailAnalysis, path: str, language: str = "english"
) -> str:
    """Format mail analysis into a concise text message"""

    # Extract just the filename from the path for the URL
    filename = os.path.basename(path)

    # Start with priority indicator
    priority_emoji = {"high": "🚨", "medium": "⚠️", "low": "ℹ️"}

    emoji = priority_emoji.get(analysis.priority, "📧")

    # Build message based on language
    if language.lower() == "spanish":
        # Spanish version
        priority_text = {"high": "ALTA", "medium": "MEDIA", "low": "BAJA"}
        message_parts = [
            f"{emoji} Correo de {analysis.sender}",
            f"Prioridad: {priority_text.get(analysis.priority, analysis.priority.upper())}",
        ]

        if analysis.action_required:
            message_parts.append("✅ ACCIÓN REQUERIDA")

        if analysis.amount:
            message_parts.append(f"💰 Monto: {analysis.amount}")

        if analysis.due_date:
            status = "⏰ VENCIDO" if analysis.is_overdue else "📅"
            message_parts.append(f"{status} Vence: {analysis.due_date}")

        # Add summary
        message_parts.append(f"\n📝 {analysis.summary}")

        message_parts.append("")
        message_parts.append("Haz clic para ver el correo:")
        message_parts.append(f"** {Config.ROOT_URL}/test_mails/{filename} **")
        message_parts.append("---")
    else:
        # English version (original)
        message_parts = [
            f"{emoji} Mail from {analysis.sender}",
            f"Priority: {analysis.priority.upper()}",
        ]

        if analysis.action_required:
            message_parts.append("✅ ACTION REQUIRED")

        if analysis.amount:
            message_parts.append(f"💰 Amount: {analysis.amount}")

        if analysis.due_date:
            status = "⏰ OVERDUE" if analysis.is_overdue else "📅"
            message_parts.append(f"{status} Due: {analysis.due_date}")

        # Add summary
        message_parts.append(f"\n📝 {analysis.summary}")

        message_parts.append("")
        message_parts.append("Click to view the mail:")
        message_parts.append(f"** {Config.ROOT_URL}/test_mails/{filename} **")
        message_parts.append("---")

    return "\n".join(message_parts)


def send_mail_summary(
    analysis: MailAnalysis,
    path: str,
    recipient_phone: Optional[str] = None,
    language: str = "english",
) -> bool:
    """
    Send mail analysis summary via Twilio SMS

    Args:
        analysis: MailAnalysis object with mail details
        recipient_phone: Phone number to send to (optional, uses config default)
        language: Language for the message (default: "english", also supports "spanish")

    Returns:
        bool: True if message sent successfully, False otherwise
    """

    # Validate Twilio configuration
    if not Config.validate_twilio_config():
        raise ValueError(
            "Twilio configuration is incomplete. Check TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER"
        )

    # Use provided recipient or default from config
    target_phone = recipient_phone or Config.RECIPIENT_PHONE
    if not target_phone:
        raise ValueError("No recipient phone number provided")

    try:
        # Initialize Twilio client
        client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)

        # Format the message
        message_body = format_mail_summary(analysis, path, language)

        # Send SMS
        message = client.messages.create(
            body=message_body, from_=Config.TWILIO_PHONE_NUMBER, to=target_phone
        )

        print(f"Message sent successfully. SID: {message.sid}")
        return True

    except Exception as e:
        print(f"Failed to send message: {e}")
        return False


def send_simple_message(text: str, recipient_phone: Optional[str] = None) -> bool:
    """
    Send a simple text message via Twilio SMS

    Args:
        text: Message text to send
        recipient_phone: Phone number to send to (optional, uses config default)

    Returns:
        bool: True if message sent successfully, False otherwise
    """

    # Validate Twilio configuration
    if not Config.validate_twilio_config():
        raise ValueError("Twilio configuration is incomplete")

    # Use provided recipient or default from config
    target_phone = recipient_phone or Config.RECIPIENT_PHONE
    if not target_phone:
        raise ValueError("No recipient phone number provided")

    try:
        # Initialize Twilio client
        client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)

        # Send SMS
        message = client.messages.create(
            body=text, from_=Config.TWILIO_PHONE_NUMBER, to=target_phone
        )

        print(f"Message sent successfully. SID: {message.sid}")
        return True

    except Exception as e:
        print(f"Failed to send message: {e}")
        return False
