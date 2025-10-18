import os
import json
import hashlib
from typing import List, Optional
from pathlib import Path
import PyPDF2


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text content from a PDF file."""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF {pdf_path}: {str(e)}")


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split text into chunks of specified size with optional overlap.

    Args:
        text: The text to chunk
        chunk_size: Maximum size of each chunk in characters
        overlap: Number of characters to overlap between chunks

    Returns:
        List of text chunks
    """
    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # If this isn't the last chunk and we're not at the end of text
        if end < len(text):
            # Try to break at a word boundary
            while end > start and text[end] not in [' ', '\n', '\t', '.', '!', '?']:
                end -= 1

            # If we couldn't find a good break point, use the original end
            if end == start:
                end = start + chunk_size

        chunk = text[start:end].strip()
        if chunk:  # Only add non-empty chunks
            chunks.append(chunk)

        # Move start position with overlap
        start = end - overlap if end < len(text) else end

    return chunks


def save_chunks_to_db(document_name: str, chunks: List[str], db_path: str = "db") -> str:
    """
    Save document chunks to the database folder structure.

    Args:
        document_name: Name of the document (without extension)
        chunks: List of text chunks
        db_path: Base path for the database folder

    Returns:
        Path to the document folder
    """
    # Create the document folder path
    doc_folder = os.path.join(db_path, document_name)
    os.makedirs(doc_folder, exist_ok=True)

    # Save each chunk as a separate file
    for i, chunk in enumerate(chunks):
        chunk_filename = f"chunk_{i:03d}.txt"
        chunk_path = os.path.join(doc_folder, chunk_filename)

        with open(chunk_path, 'w', encoding='utf-8') as f:
            f.write(chunk)

    # Save metadata about the chunks
    metadata = {
        "document_name": document_name,
        "total_chunks": len(chunks),
        "chunk_size": 500,
        "created_at": None,  # Will be set when called
        "chunks": [f"chunk_{i:03d}.txt" for i in range(len(chunks))]
    }

    metadata_path = os.path.join(doc_folder, "metadata.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    return doc_folder


def process_pdf_to_chunks(pdf_path: str, db_path: str = "db", chunk_size: int = 500) -> str:
    """
    Process a PDF file: extract text, chunk it, and save to database.

    Args:
        pdf_path: Path to the PDF file
        db_path: Base path for the database folder
        chunk_size: Size of each chunk in characters

    Returns:
        Path to the document folder containing chunks
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    # Extract document name without extension
    document_name = Path(pdf_path).stem

    # Extract text from PDF
    text = extract_text_from_pdf(pdf_path)

    if not text:
        raise ValueError(f"No text could be extracted from {pdf_path}")

    # Chunk the text
    chunks = chunk_text(text, chunk_size)

    if not chunks:
        raise ValueError(f"No chunks generated from {pdf_path}")

    # Save chunks to database
    doc_folder = save_chunks_to_db(document_name, chunks, db_path)

    print(f"✅ Processed {document_name}: {len(chunks)} chunks saved to {doc_folder}")

    return doc_folder


def process_multiple_pdfs_to_chunks(pdf_directory: str, db_path: str = "db", chunk_size: int = 500) -> List[str]:
    """
    Process multiple PDF files in a directory.

    Args:
        pdf_directory: Directory containing PDF files
        db_path: Base path for the database folder
        chunk_size: Size of each chunk in characters

    Returns:
        List of document folder paths
    """
    if not os.path.isdir(pdf_directory):
        raise ValueError(f"Directory not found: {pdf_directory}")

    # Find all PDF files
    pdf_files = [f for f in os.listdir(pdf_directory) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print(f"No PDF files found in {pdf_directory}")
        return []

    print(f"Found {len(pdf_files)} PDF files to process for chunking")

    processed_folders = []

    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_directory, pdf_file)
        print(f"\n📄 Processing: {pdf_file}")

        try:
            doc_folder = process_pdf_to_chunks(pdf_path, db_path, chunk_size)
            processed_folders.append(doc_folder)
        except Exception as e:
            print(f"❌ Error processing {pdf_file}: {e}")

    return processed_folders