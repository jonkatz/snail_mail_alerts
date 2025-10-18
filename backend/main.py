from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import OpenAI
import os

from messaging import send_simple_message
from config import Config
from mail_processor import process_multiple_mails
from document_chunker import process_multiple_pdfs_to_chunks
from document_search import DocumentSearcher

app = FastAPI(
    title="SMS Messaging API", description="Simple SMS messaging using SlickText API"
)

# Mount static files directory for serving PDFs
# This makes PDFs accessible at /test_mails/<filename>.pdf
test_mails_path = os.path.join(os.path.dirname(__file__), "test_mails")
app.mount("/test_mails", StaticFiles(directory=test_mails_path), name="test_mails")


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
            "/health": "Check system configuration",
            "/process-mails": "Process all mails and send SMS notifications (English)",
            "/process-mails-spanish": "Process all mails and send SMS notifications (Spanish)",
            "/db-stats": "Get document database statistics",
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
            raise ValueError(
                "OpenAI configuration is incomplete. Check OPEN_AI API key"
            )

        # Initialize OpenAI client
        client = OpenAI(api_key=Config.OPENAI_API_KEY)

        # Search for relevant document context
        searcher = DocumentSearcher("db")
        document_context = searcher.get_context_for_ai(request.question, max_chunks=3)

        # Prepare system message with document context
        system_message = """You are a helpful assistant that can answer questions about documents.
        You have access to processed mail and document content. Keep responses concise and under 160 characters when possible for SMS.
        If the user's question relates to documents in the system, use that information to provide accurate answers.
        If no relevant documents are found, let the user know that no relevant documents were found. Never be ambiguous."""

        # Prepare messages with document context
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Context: {document_context}\n\nQuestion: {request.question}"}
        ]

        # Create chat completion
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using mini for cost efficiency
            messages=messages,
            max_tokens=200,  # Increased slightly for document-based responses
            temperature=0.7,
        )

        # Get the AI response
        ai_response = response.choices[0].message.content

        # Send the AI response via SMS
        sms_success = send_simple_message(f"AI: {ai_response}", request.recipient_phone)

        if sms_success:
            return {
                "status": "success",
                "message": "AI response sent via SMS",
                "ai_response": ai_response,
            }
        else:
            return {
                "status": "partial_success",
                "message": "AI responded but SMS failed",
                "ai_response": ai_response,
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
    """Process all mails in the mail directory and chunk documents"""
    try:
        # Process mails for analysis and SMS notifications
        mail_results = process_multiple_mails(Config.MAIL_DIRECTORY, Config.RECIPIENT_PHONE, True)

        # # Chunk documents and save to db folder
        # chunked_folders = process_multiple_pdfs_to_chunks(Config.MAIL_DIRECTORY, "db", 500)

        return {
            "status": "success",
            "message": "Mails processed and chunked successfully",
            "mail_analyses": len(mail_results),
            # "documents_chunked": len(chunked_folders),
            # "chunked_folders": chunked_folders
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.get("/db-stats")
def get_database_stats():
    """Get statistics about the document database"""
    try:
        searcher = DocumentSearcher("db")
        stats = searcher.get_database_stats()
        return {
            "status": "success",
            "database_stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.get("/process-mails-spanish")
def process_mails_spanish():
    """Process all mails in the mail directory (Spanish - análisis y mensajes en español)"""
    try:
        process_multiple_mails(
            Config.MAIL_DIRECTORY, Config.RECIPIENT_PHONE, False, "spanish"
        )
        return {"status": "success", "message": "Correos procesados exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
