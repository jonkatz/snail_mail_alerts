import os
import json
from typing import List, Dict, Tuple
from pathlib import Path
import re


class DocumentSearcher:
    """Search through chunked documents in the database."""

    def __init__(self, db_path: str = "db"):
        self.db_path = db_path

    def get_all_documents(self) -> List[str]:
        """Get list of all document names in the database."""
        if not os.path.exists(self.db_path):
            return []

        documents = []
        for item in os.listdir(self.db_path):
            doc_path = os.path.join(self.db_path, item)
            if os.path.isdir(doc_path):
                documents.append(item)

        return documents

    def get_document_chunks(self, document_name: str) -> List[Dict]:
        """Get all chunks for a specific document."""
        doc_path = os.path.join(self.db_path, document_name)

        if not os.path.exists(doc_path):
            return []

        # Load metadata
        metadata_path = os.path.join(doc_path, "metadata.json")
        metadata = {}
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

        chunks = []
        chunk_files = [f for f in os.listdir(doc_path) if f.startswith("chunk_") and f.endswith(".txt")]
        chunk_files.sort()  # Ensure proper order

        for chunk_file in chunk_files:
            chunk_path = os.path.join(doc_path, chunk_file)
            with open(chunk_path, 'r', encoding='utf-8') as f:
                content = f.read()

            chunk_info = {
                "document": document_name,
                "chunk_file": chunk_file,
                "content": content,
                "chunk_index": int(chunk_file.split("_")[1].split(".")[0])
            }
            chunks.append(chunk_info)

        return chunks

    def search_chunks_by_keywords(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Search chunks using keyword matching.

        Args:
            query: Search query
            max_results: Maximum number of chunks to return

        Returns:
            List of matching chunks with relevance scores
        """
        query_words = query.lower().split()
        results = []

        documents = self.get_all_documents()

        for doc_name in documents:
            chunks = self.get_document_chunks(doc_name)

            for chunk in chunks:
                content_lower = chunk["content"].lower()

                # Simple keyword matching with scoring
                score = 0
                matches = []

                for word in query_words:
                    word_count = content_lower.count(word)
                    if word_count > 0:
                        score += word_count
                        matches.append(word)

                if score > 0:
                    chunk["relevance_score"] = score
                    chunk["matched_keywords"] = matches
                    results.append(chunk)

        # Sort by relevance score (descending)
        results.sort(key=lambda x: x["relevance_score"], reverse=True)

        return results[:max_results]

    def search_chunks_fuzzy(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Search chunks using fuzzy/partial matching.

        Args:
            query: Search query
            max_results: Maximum number of chunks to return

        Returns:
            List of matching chunks with relevance scores
        """
        query_lower = query.lower()
        results = []

        documents = self.get_all_documents()

        for doc_name in documents:
            chunks = self.get_document_chunks(doc_name)

            for chunk in chunks:
                content_lower = chunk["content"].lower()

                # Check for partial matches and phrases
                score = 0

                # Exact phrase match gets high score
                if query_lower in content_lower:
                    score += 10

                # Individual word matches
                query_words = query_lower.split()
                for word in query_words:
                    if len(word) > 2:  # Ignore very short words
                        word_count = content_lower.count(word)
                        score += word_count * 2

                # Partial word matches using regex
                for word in query_words:
                    if len(word) > 3:
                        pattern = re.compile(re.escape(word[:3]), re.IGNORECASE)
                        partial_matches = len(pattern.findall(content_lower))
                        score += partial_matches * 0.5

                if score > 0:
                    chunk["relevance_score"] = score
                    results.append(chunk)

        # Sort by relevance score (descending)
        results.sort(key=lambda x: x["relevance_score"], reverse=True)

        return results[:max_results]

    def get_context_for_ai(self, query: str, max_chunks: int = 3) -> str:
        """
        Get relevant document context for AI responses.

        Args:
            query: User's question
            max_chunks: Maximum number of chunks to include

        Returns:
            Formatted context string for AI
        """
        relevant_chunks = self.search_chunks_fuzzy(query, max_chunks)

        if not relevant_chunks:
            return "No relevant documents found in the database."

        context_parts = []
        context_parts.append("Based on the following documents in your system:")
        context_parts.append("")

        for i, chunk in enumerate(relevant_chunks, 1):
            context_parts.append(f"Document {i}: {chunk['document']} (Chunk {chunk['chunk_index']})")
            context_parts.append(f"Content: {chunk['content'][:400]}...")  # Limit chunk size for context
            context_parts.append("")

        context_parts.append("Please answer the user's question based on the above document content.")

        return "\n".join(context_parts)

    def get_database_stats(self) -> Dict:
        """Get statistics about the document database."""
        documents = self.get_all_documents()
        total_chunks = 0

        for doc_name in documents:
            chunks = self.get_document_chunks(doc_name)
            total_chunks += len(chunks)

        return {
            "total_documents": len(documents),
            "total_chunks": total_chunks,
            "documents": documents
        }