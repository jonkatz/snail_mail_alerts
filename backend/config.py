import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration management for the mail analysis and messaging system"""

    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Twilio Configuration
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE", "")

    # Recipient Configuration
    RECIPIENT_PHONE: str = os.getenv("RECIPIENT_CONTACT", "")

    # Mail Directory Configuration
    MAIL_DIRECTORY: str = os.getenv("MAIL_DIRECTORY", "")

    @classmethod
    def validate_openai_config(cls) -> bool:
        """Check if OpenAI configuration is valid"""
        return bool(cls.OPENAI_API_KEY)

    @classmethod
    def validate_twilio_config(cls) -> bool:
        """Check if Twilio configuration is valid"""
        return all(
            [cls.TWILIO_ACCOUNT_SID, cls.TWILIO_AUTH_TOKEN, cls.TWILIO_PHONE_NUMBER]
        )

    @classmethod
    def validate_recipient_config(cls) -> bool:
        """Check if recipient configuration is valid"""
        return bool(cls.RECIPIENT_PHONE)
