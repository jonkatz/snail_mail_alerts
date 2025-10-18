from typing import Union, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import tempfile
import os

from messaging import send_mail_summary, send_simple_message
from mail_processor import process_mail, process_multiple_mails
from analyze_mail import analyze_mail_pdf, MailAnalysis
from config import Config

app = FastAPI(title="Snail Mail Alerts API", description="AI-powered mail analysis and messaging system")


class MessageRequest(BaseModel):
    text: str
    recipient_phone: Optional[str] = None


class MailProcessRequest(BaseModel):
    recipient_phone: Optional[str] = None
    send_all: bool = False


@app.get("/")
def read_root():
    return {
        "message": "Snail Mail Alerts API",
        "version": "1.0.0",
        "endpoints": {
            "/send-message": "Send simple SMS message",
            "/analyze-mail": "Upload and analyze mail PDF",
            "/process-mail": "Analyze mail and send summary if important",
            "/health": "Check system configuration"
        }
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


@app.post("/analyze-mail")
def analyze_mail(file: UploadFile = File(...)):
    """Upload and analyze a mail PDF"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            content = file.file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        # Analyze the mail
        analysis = analyze_mail_pdf(temp_path)

        # Clean up temp file
        os.unlink(temp_path)

        return {
            "status": "success",
            "analysis": {
                "important": analysis.important,
                "action_required": analysis.action_required,
                "sender": analysis.sender,
                "due_date": analysis.due_date,
                "is_overdue": analysis.is_overdue,
                "amount": analysis.amount,
                "priority": analysis.priority,
                "summary": analysis.summary
            }
        }
    except Exception as e:
        # Clean up temp file if it exists
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/process-mail")
def process_mail_endpoint(request: MailProcessRequest, file: UploadFile = File(...)):
    """Upload, analyze mail PDF and send SMS summary if important"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            content = file.file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        # Process the mail (analyze + send message if needed)
        analysis = process_mail(temp_path, request.recipient_phone, request.send_all)

        # Clean up temp file
        os.unlink(temp_path)

        # Determine if message was sent
        message_sent = request.send_all or analysis.important

        return {
            "status": "success",
            "message_sent": message_sent,
            "analysis": {
                "important": analysis.important,
                "action_required": analysis.action_required,
                "sender": analysis.sender,
                "due_date": analysis.due_date,
                "is_overdue": analysis.is_overdue,
                "amount": analysis.amount,
                "priority": analysis.priority,
                "summary": analysis.summary
            }
        }
    except Exception as e:
        # Clean up temp file if it exists
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.get("/health")
def health_check():
    """Check system configuration and health"""
    return {
        "status": "healthy",
        "configuration": {
            "openai_configured": Config.validate_openai_config(),
            "twilio_configured": Config.validate_twilio_config(),
            "recipient_configured": Config.validate_recipient_config()
        }
    }