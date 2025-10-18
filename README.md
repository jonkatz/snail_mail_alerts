# Snail Mail Alerts

Analyzes PDF mail documents using OpenAI's vision API to determine if they're important (bills, official documents) or not important (junk mail, newsletters, offers).

## Features

- 📄 Analyzes PDF mail documents
- 🤖 Uses OpenAI GPT-4o with vision capabilities
- 🔍 Extracts key information: sender, due dates, amounts, priority
- ✅ Identifies if action is required
- ⚠️ Detects overdue items
- 🎯 Distinguishes important mail from junk

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set up your OpenAI API key:

```bash
cp .env.example .env
# Edit .env and add your API key
```

Or export it in your shell:

```bash
export OPENAI_API_KEY="your_api_key_here"
```

## Usage

### Command Line

```bash
python analyze_mail.py path/to/mail.pdf
```

### Python API

```python
from analyze_mail import analyze_mail_pdf

# Analyze a mail PDF
result = analyze_mail_pdf("path/to/mail.pdf")

print(f"Important: {result.important}")
print(f"Action Required: {result.action_required}")
print(f"Sender: {result.sender}")
print(f"Priority: {result.priority}")
print(f"Summary: {result.summary}")

if result.due_date:
    print(f"Due Date: {result.due_date}")
    print(f"Overdue: {result.is_overdue}")

if result.amount:
    print(f"Amount: {result.amount}")
```

## Mail Classification

### Important Mail ✓

- Bills
- Invoices
- Official government documents
- Legal notices
- Tax documents
- Medical statements
- Financial statements
- Urgent notices requiring action

### Not Important Mail ✗

- Junk mail
- Promotional offers
- Newsletters
- Magazines
- Catalogs
- Advertisements
- Solicitations

## Response Fields

The `MailAnalysis` object contains:

- `important` (bool): True if mail is important, False otherwise
- `action_required` (bool): True if recipient needs to take action
- `sender` (str): Name of the sender/organization
- `due_date` (str, optional): Due date in ISO format (YYYY-MM-DD)
- `is_overdue` (bool): True if the item is overdue
- `amount` (str, optional): Dollar amount if applicable (e.g., "$125.50")
- `priority` (str): "high", "medium", or "low"
- `summary` (str): Brief summary of the mail content and any actions needed

## Requirements

- Python 3.8+
- OpenAI API key
- Internet connection for API calls

## Note on PDF Processing

The function uses OpenAI's vision API with PDFs encoded as base64. The model can analyze the visual layout and text content of the PDF to make intelligent classifications.
