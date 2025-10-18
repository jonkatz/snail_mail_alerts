import base64
import os
from typing import Optional
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class MailAnalysis(BaseModel):
    """Data model for mail analysis results"""

    important: bool
    action_required: bool
    sender: str
    due_date: Optional[str] = None
    is_overdue: bool = False
    amount: Optional[str] = None
    priority: str  # e.g., "high", "medium", "low"
    summary: str


def analyze_mail_pdf(
    pdf_path: str, api_key: Optional[str] = None, language: str = "english"
) -> MailAnalysis:
    """
    Analyzes a PDF of mail to determine if it's important (bill, official document)
    or not important (junk mail, offers, newsletters, magazines).

    Args:
        pdf_path: Path to the PDF file to analyze
        api_key: OpenAI API key (if not provided, uses OPENAI_API_KEY env var)
        language: Language for the analysis output (default: "english", also supports "spanish")

    Returns:
        MailAnalysis object with analysis results

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If API key is not provided
    """
    # Validate PDF exists
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    # Get API key
    if api_key is None:
        api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OpenAI API key must be provided or set in OPENAI_API_KEY environment variable"
        )

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)

    # Upload the PDF file to OpenAI
    with open(pdf_path, "rb") as pdf_file:
        file_response = client.files.create(file=pdf_file, purpose="user_data")

    file_id = file_response.id

    # Define the tool/function schema for OpenAI responses API
    tools = [
        {
            "type": "function",
            "name": "is_important",
            "description": """Classify mail as important or not important. 
            Important mail includes: bills, invoices, official government documents, 
            legal notices, tax documents, medical statements, financial statements, 
            urgent notices requiring action.
            
            Not important mail includes: junk mail, promotional offers, newsletters, 
            magazines, catalogs, advertisements, solicitations.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "important": {
                        "type": "boolean",
                        "description": "True if mail is important (bill, official document, etc.), False if not important (junk mail, offers, newsletters, magazines)",
                    },
                    "action_required": {
                        "type": "boolean",
                        "description": "True if recipient needs to take action (pay bill, respond, etc.)",
                    },
                    "sender": {
                        "type": "string",
                        "description": "Name of the sender/organization",
                    },
                    "due_date": {
                        "type": "string",
                        "description": "Due date if applicable (ISO format YYYY-MM-DD), null if not applicable",
                    },
                    "is_overdue": {
                        "type": "boolean",
                        "description": "True if the item is overdue based on current date",
                    },
                    "amount": {
                        "type": "string",
                        "description": "Dollar amount if applicable (e.g., '$125.50'), null if not applicable",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "Priority level: high (urgent/overdue), medium (action needed soon), low (informational/not urgent)",
                    },
                    "summary": {
                        "type": "string",
                        "description": "Brief summary of the mail content and any actions needed",
                    },
                },
                "required": [
                    "important",
                    "action_required",
                    "sender",
                    "is_overdue",
                    "priority",
                    "summary",
                ],
            },
        }
    ]

    # Create the response with PDF file and function calling
    try:
        # Set the prompt based on language
        if language.lower() == "spanish":
            prompt_text = """Analiza este documento de correo y determina si es importante o no importante.

El correo importante incluye: facturas, recibos, documentos oficiales del gobierno, avisos legales, 
documentos fiscales, estados de cuenta médicos, estados financieros, avisos urgentes.

El correo no importante incluye: correo basura, ofertas promocionales, boletines informativos, revistas, 
catálogos, anuncios, solicitudes.

Usa la función is_important para clasificar este documento con todos los detalles relevantes. 
IMPORTANTE: Proporciona el resumen (summary) en español."""
        else:
            prompt_text = """Analyze this mail document and determine if it's important or not important.

Important mail includes: bills, invoices, official government documents, legal notices, 
tax documents, medical statements, financial statements, urgent notices.

Not important mail includes: junk mail, promotional offers, newsletters, magazines, 
catalogs, advertisements, solicitations.

Use the is_important function to classify this document with all relevant details."""

        input_list = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_file",
                        "file_id": file_id,
                    },
                    {
                        "type": "input_text",
                        "text": prompt_text,
                    },
                ],
            }
        ]

        response = client.responses.create(
            model="gpt-4o",  # gpt-4o supports PDF processing
            input=input_list,
            tools=tools,
            tool_choice="required",
        )
    finally:
        # Clean up: delete the uploaded file
        try:
            client.files.delete(file_id)
        except:
            pass  # Ignore cleanup errors

    # Extract the function call result from response.output
    import json

    arguments = None
    for item in response.output:
        if item.type == "function_call" and item.name == "is_important":
            arguments = json.loads(item.arguments)
            break

    if arguments is None:
        raise ValueError("OpenAI did not return a function call for is_important")

    # Create and return MailAnalysis object
    return MailAnalysis(**arguments)


def main():
    """Example usage"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python analyze_mail.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    try:
        result = analyze_mail_pdf(pdf_path)

        print("\n" + "=" * 50)
        print("MAIL ANALYSIS RESULTS")
        print("=" * 50)
        print(f"Important: {'✓ YES' if result.important else '✗ NO'}")
        print(f"Action Required: {'✓ YES' if result.action_required else '✗ NO'}")
        print(f"Sender: {result.sender}")
        print(f"Priority: {result.priority.upper()}")

        if result.due_date and result.due_date not in [".", "N/A", "None", ""]:
            print(f"Due Date: {result.due_date}")
            if result.is_overdue:
                print("Status: ⚠️  OVERDUE")

        if result.amount:
            print(f"Amount: {result.amount}")

        print(f"\nSummary: {result.summary}")
        print("=" * 50 + "\n")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
