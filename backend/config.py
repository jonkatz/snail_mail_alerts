import os
from typing import Optional


class Config:
    """Configuration management for the mail analysis and messaging system"""

    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Twilio Configuration
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")

    # Recipient Configuration
    RECIPIENT_PHONE: str = os.getenv("RECIPIENT_PHONE", "")

    @classmethod
    def validate_openai_config(cls) -> bool:
        """Check if OpenAI configuration is valid"""
        return bool(cls.OPENAI_API_KEY)

    @classmethod
    def validate_twilio_config(cls) -> bool:
        """Check if Twilio configuration is valid"""
        return all([
            cls.TWILIO_ACCOUNT_SID,
            cls.TWILIO_AUTH_TOKEN,
            cls.TWILIO_PHONE_NUMBER
        ])

    @classmethod
    def validate_recipient_config(cls) -> bool:
        """Check if recipient configuration is valid"""
        return bool(cls.RECIPIENT_PHONE)