import base64
import os
from typing import Optional
from openai import OpenAI
from pydantic import BaseModel


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


def analyze_mail_pdf(pdf_path: str, api_key: Optional[str] = None) -> MailAnalysis:
    """
    Analyzes a PDF of mail to determine if it's important (bill, official document)
    or not important (junk mail, offers, newsletters, magazines).

    Args:
        pdf_path: Path to the PDF file to analyze
        api_key: OpenAI API key (if not provided, uses OPENAI_API_KEY env var)

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

    # Read and encode PDF as base64
    with open(pdf_path, "rb") as pdf_file:
        pdf_data = base64.b64encode(pdf_file.read()).decode("utf-8")

    # Define the tool/function schema for OpenAI
    tools = [
        {
            "type": "function",
            "function": {
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
            },
        }
    ]

    # Create the chat completion with vision and function calling
    response = client.chat.completions.create(
        model="gpt-4o",  # gpt-4o supports vision and function calling
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Analyze this mail document and determine if it's important or not important.

Important mail includes: bills, invoices, official government documents, legal notices, 
tax documents, medical statements, financial statements, urgent notices.

Not important mail includes: junk mail, promotional offers, newsletters, magazines, 
catalogs, advertisements, solicitations.

Use the is_important function to classify this document with all relevant details.""",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:application/pdf;base64,{pdf_data}"},
                    },
                ],
            }
        ],
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "is_important"}},
    )

    # Extract the function call result
    message = response.choices[0].message
    if not message.tool_calls:
        raise ValueError("OpenAI did not return a function call")

    tool_call = message.tool_calls[0]
    import json

    arguments = json.loads(tool_call.function.arguments)

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

        if result.due_date:
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
