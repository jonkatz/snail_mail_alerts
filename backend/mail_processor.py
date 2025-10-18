import os
import sys
from typing import Optional
from analyze_mail import analyze_mail_pdf, MailAnalysis
from messaging import send_mail_summary, send_simple_message
from config import Config


def process_mail(pdf_path: str, recipient_phone: Optional[str] = None, send_all: bool = False) -> MailAnalysis:
    """
    Process a mail PDF: analyze it and send summary if important

    Args:
        pdf_path: Path to the PDF file to analyze
        recipient_phone: Phone number to send to (optional, uses config default)
        send_all: If True, send summary for all mail. If False, only send for important mail

    Returns:
        MailAnalysis: The analysis results

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If configuration is invalid
    """

    # Validate configurations
    if not Config.validate_openai_config():
        raise ValueError("OpenAI API key not configured. Set OPENAI_API_KEY environment variable")

    if not Config.validate_twilio_config():
        raise ValueError("Twilio configuration incomplete. Check TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER")

    if not recipient_phone and not Config.validate_recipient_config():
        raise ValueError("No recipient phone number configured. Set RECIPIENT_PHONE environment variable or provide recipient_phone parameter")

    # Analyze the mail
    print(f"Analyzing mail: {pdf_path}")
    analysis = analyze_mail_pdf(pdf_path)

    # Print analysis results
    print("\n" + "=" * 50)
    print("MAIL ANALYSIS RESULTS")
    print("=" * 50)
    print(f"Important: {'✓ YES' if analysis.important else '✗ NO'}")
    print(f"Action Required: {'✓ YES' if analysis.action_required else '✗ NO'}")
    print(f"Sender: {analysis.sender}")
    print(f"Priority: {analysis.priority.upper()}")

    if analysis.due_date:
        print(f"Due Date: {analysis.due_date}")
        if analysis.is_overdue:
            print("Status: ⚠️  OVERDUE")

    if analysis.amount:
        print(f"Amount: {analysis.amount}")

    print(f"\nSummary: {analysis.summary}")
    print("=" * 50)

    # Decide whether to send message
    should_send = send_all or analysis.important

    if should_send:
        print(f"\nSending {'important ' if analysis.important else ''}mail summary...")
        success = send_mail_summary(analysis, recipient_phone)
        if success:
            print("✅ Message sent successfully!")
        else:
            print("❌ Failed to send message")
    else:
        print(f"\n📧 Mail not important - no message sent")

    return analysis


def process_multiple_mails(pdf_directory: str, recipient_phone: Optional[str] = None, send_all: bool = False) -> list[MailAnalysis]:
    """
    Process multiple mail PDFs in a directory

    Args:
        pdf_directory: Directory containing PDF files
        recipient_phone: Phone number to send to (optional, uses config default)
        send_all: If True, send summary for all mail. If False, only send for important mail

    Returns:
        list[MailAnalysis]: List of analysis results for each PDF
    """

    if not os.path.isdir(pdf_directory):
        raise ValueError(f"Directory not found: {pdf_directory}")

    # Find all PDF files
    pdf_files = [f for f in os.listdir(pdf_directory) if f.lower().endswith('.pdf')]

    if not pdf_files:
        print(f"No PDF files found in {pdf_directory}")
        return []

    print(f"Found {len(pdf_files)} PDF files to process")

    results = []
    important_count = 0

    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_directory, pdf_file)
        print(f"\n{'='*60}")
        print(f"Processing: {pdf_file}")
        print(f"{'='*60}")

        try:
            analysis = process_mail(pdf_path, recipient_phone, send_all)
            results.append(analysis)

            if analysis.important:
                important_count += 1

        except Exception as e:
            print(f"Error processing {pdf_file}: {e}")

    # Send summary message
    if results:
        summary_text = f"📬 Processed {len(results)} mail items. {important_count} important items found."
        send_simple_message(summary_text, recipient_phone)

    return results


def main():
    """Command line interface for mail processing"""

    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single file: python mail_processor.py <pdf_path> [recipient_phone] [--send-all]")
        print("  Directory:   python mail_processor.py --dir <directory_path> [recipient_phone] [--send-all]")
        print("")
        print("Options:")
        print("  --send-all    Send summaries for all mail (not just important)")
        print("  --dir         Process all PDFs in directory")
        sys.exit(1)

    args = sys.argv[1:]
    send_all = "--send-all" in args
    if send_all:
        args.remove("--send-all")

    directory_mode = "--dir" in args
    if directory_mode:
        args.remove("--dir")

    if not args:
        print("Error: Path argument required")
        sys.exit(1)

    path = args[0]
    recipient_phone = args[1] if len(args) > 1 else None

    try:
        if directory_mode:
            results = process_multiple_mails(path, recipient_phone, send_all)
            print(f"\n🎉 Processed {len(results)} files successfully!")
        else:
            result = process_mail(path, recipient_phone, send_all)
            print(f"\n🎉 Processing complete!")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()