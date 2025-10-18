from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI

from messaging import send_simple_message
from config import Config
from mail_processor import process_multiple_mails

app = FastAPI(
    title="SMS Messaging API", description="Simple SMS messaging using SlickText API"
)


class MessageRequest(BaseModel):
    text: str
    recipient_phone: Optional[str] = None


class ChatRequest(BaseModel):
    question: str
    recipient_phone: Optional[str] = None


@app.get("/")
def read_root():
    return {
        "message": "SMS Messaging API",
        "version": "1.0.0",
        "endpoints": {
            "/send-message": "Send simple SMS message",
            "/ask-ai": "Ask OpenAI a question and get response via SMS",
            "/health": "Check system configuration"
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


@app.post("/ask-ai")
def ask_ai(request: ChatRequest):
    """Ask OpenAI a question and send the response via SMS"""
    try:
        # Validate OpenAI configuration
        if not Config.validate_openai_config():
            raise ValueError("OpenAI configuration is incomplete. Check OPEN_AI API key")

        # Initialize OpenAI client
        client = OpenAI(api_key=Config.OPENAI_API_KEY)

        # Create chat completion
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using mini for cost efficiency
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Keep responses concise and under 160 characters when possible for SMS."
                },
                {
                    "role": "user",
                    "content": request.question
                }
            ],
            max_tokens=150,
            temperature=0.7
        )

        # Get the AI response
        ai_response = response.choices[0].message.content

        # Send the AI response via SMS
        sms_success = send_simple_message(
            f"AI: {ai_response}",
            request.recipient_phone
        )

        if sms_success:
            return {
                "status": "success",
                "message": "AI response sent via SMS",
                "ai_response": ai_response
            }
        else:
            return {
                "status": "partial_success",
                "message": "AI responded but SMS failed",
                "ai_response": ai_response
            }

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
            "openai_configured": Config.validate_openai_config(),
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
