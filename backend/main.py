from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from messaging import send_simple_message
from config import Config
from mail_processor import process_multiple_mails

app = FastAPI(
    title="SMS Messaging API", description="Simple SMS messaging using SlickText API"
)


class MessageRequest(BaseModel):
    text: str
    recipient_phone: Optional[str] = None


@app.get("/")
def read_root():
    return {
        "message": "SMS Messaging API",
        "version": "1.0.0",
        "endpoints": {
            "/send-message": "Send simple SMS message",
            "/health": "Check system configuration",
        },
    }


@app.post("/send-message")
def send_message(request: MessageRequest):
    """Send a simple SMS message via Twilio"""
    try:
        success = send_simple_message(request.text, request.recipient_phone)
        if success:
            return {"status": "success", "message": "SMS sent successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send SMS")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.get("/health")
def health_check():
    """Check system configuration and health"""
    return {
        "status": "healthy",
        "configuration": {
            "twilio_configured": Config.validate_twilio_config(),
            "recipient_configured": Config.validate_recipient_config(),
        },
    }


@app.get("/process-mails")
def process_mails():
    """Process all mails in the mail directory"""
    try:
        process_multiple_mails(Config.MAIL_DIRECTORY, Config.RECIPIENT_PHONE, True)
        return {"status": "success", "message": "Mails processed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
