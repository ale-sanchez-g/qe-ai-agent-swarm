"""
Product Knowledge Base for Chat App
Provides long-term memory capabilities for product information like loans, services, etc.
"""

import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import threading
import hashlib

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    import torch
except ImportError as e:
    chromadb = None
    SentenceTransformer = None
    torch = None
    _IMPORT_ERROR = e
else:
    _IMPORT_ERROR = None


class ProductKnowledgeBase:
    """
    Long-term memory system for product information using vector embeddings.
    
    Features:
    - Stores product documents (txt, md files) with vector embeddings
    - Enables semantic search for relevant product information
    - Supports different product categories (loans, services, etc.)
    - Thread-safe operations
    """

    def __init__(
        self,
        persist_dir: str = "knowledge_base",
        collection_name: str = "product_knowledge",
        model_name: str = "all-MiniLM-L6-v2"
    ):
        if chromadb is None or SentenceTransformer is None:
            raise RuntimeError(
                f"ProductKnowledgeBase dependencies missing. Please install: pip install chromadb sentence-transformers\n"
                f"Original error: {_IMPORT_ERROR}"
            )

        self.persist_dir = persist_dir
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)

        # Initialize embedding model with device handling to fix meta tensor issue
        try:
            # Determine the appropriate device
            if torch is not None and torch.cuda.is_available():
                device = "cuda"
            elif torch is not None and hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                device = "mps"  # Apple Silicon GPU
            else:
                device = "cpu"
            
            # Load model with explicit device specification
            self.embedder = SentenceTransformer(model_name, device=device)
            
            # Ensure model is properly loaded and not on meta device
            if hasattr(self.embedder, '_modules'):
                for module in self.embedder.modules():
                    if hasattr(module, 'device') and str(module.device) == 'meta':
                        # Force re-initialization if any module is on meta device
                        self.embedder = SentenceTransformer(model_name, device='cpu')
                        break
                        
        except Exception as e:
            # Fallback to CPU with explicit device setting
            print(f"Warning: Failed to initialize embedder with optimal device, falling back to CPU: {e}")
            self.embedder = SentenceTransformer(model_name, device='cpu')

        # Initialize Chroma persistent client/collection
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(allow_reset=False)
        )
        
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Product knowledge base for customer support"}
        )

        self._lock = threading.Lock()

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts"""
        try:
            return self.embedder.encode(texts, normalize_embeddings=True).tolist()
        except Exception as e:
            if "meta tensor" in str(e) or "Cannot copy out of meta tensor" in str(e):
                # Reinitialize the model if we encounter meta tensor issues
                print(f"Warning: Reinitializing embedder due to meta tensor issue: {e}")
                try:
                    model_name = getattr(self.embedder, 'model_name', 'all-MiniLM-L6-v2')
                    self.embedder = SentenceTransformer(model_name, device='cpu')
                    return self.embedder.encode(texts, normalize_embeddings=True).tolist()
                except Exception as reinit_error:
                    raise RuntimeError(f"Failed to reinitialize embedder: {reinit_error}") from e
            else:
                raise e

    def add_document(
        self,
        content: str,
        filename: str,
        product_category: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a single document to the knowledge base.
        
        Args:
            content: The text content of the document
            filename: Name of the source file
            product_category: Category (e.g., 'home_loans', 'car_loans', 'services')
            metadata: Additional metadata for the document
        
        Returns:
            Document ID
        """
        if not content.strip():
            raise ValueError("Document content cannot be empty")

        # Create document ID based on content hash for deduplication
        content_hash = hashlib.md5(content.encode()).hexdigest()
        doc_id = f"{product_category}::{filename}::{content_hash}"

        # Prepare metadata
        doc_metadata = {
            "filename": filename,
            "product_category": product_category,
            "added_at": int(time.time()),
            "content_length": len(content),
            **(metadata or {})
        }

        # Generate embedding
        try:
            embedding = self.embed([content])[0]
        except Exception as e:
            raise RuntimeError(f"Failed to generate embedding for document: {e}") from e

        # Store in vector database
        with self._lock:
            self.collection.upsert(
                ids=[doc_id],
                documents=[content],
                embeddings=[embedding],
                metadatas=[doc_metadata]
            )

        return doc_id

    def add_documents_from_folder(
        self,
        folder_path: str,
        product_category: str = "general",
        file_patterns: List[str] = None,
        max_file_size: int = 1_000_000  # 1MB default
    ) -> Dict[str, Any]:
        """
        Bulk add documents from a folder.
        
        Args:
            folder_path: Path to folder containing documents
            product_category: Category for all documents in this folder
            file_patterns: List of glob patterns (default: ['*.txt', '*.md'])
            max_file_size: Maximum file size in bytes
        
        Returns:
            Dictionary with ingestion results
        """
        if file_patterns is None:
            file_patterns = ['*.txt', '*.md']

        folder = Path(folder_path)
        if not folder.exists():
            raise ValueError(f"Folder does not exist: {folder_path}")

        results = {
            "processed": 0,
            "skipped": 0,
            "errors": [],
            "document_ids": []
        }

        for pattern in file_patterns:
            for file_path in folder.glob(pattern):
                try:
                    # Check file size
                    if file_path.stat().st_size > max_file_size:
                        results["skipped"] += 1
                        results["errors"].append(f"File too large: {file_path.name}")
                        continue

                    # Read and process file
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    
                    if not content.strip():
                        results["skipped"] += 1
                        results["errors"].append(f"Empty file: {file_path.name}")
                        continue

                    # Add document
                    doc_id = self.add_document(
                        content=content,
                        filename=file_path.name,
                        product_category=product_category,
                        metadata={"file_path": str(file_path)}
                    )

                    results["document_ids"].append(doc_id)
                    results["processed"] += 1

                except Exception as e:
                    results["skipped"] += 1
                    results["errors"].append(f"Error processing {file_path.name}: {str(e)}")

        return results

    def search_knowledge(
        self,
        query: str,
        product_category: Optional[str] = None,
        max_results: int = 5,
        min_similarity: float = 0.2  # Lowered from 0.7 to 0.2 for better results
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant product information.
        
        Args:
            query: Search query
            product_category: Filter by specific product category
            max_results: Maximum number of results to return
            min_similarity: Minimum similarity score (0-1)
        
        Returns:
            List of relevant documents with metadata
        """
        if not query.strip():
            return []

        # Generate query embedding
        try:
            query_embedding = self.embed([query])[0]
        except Exception as e:
            raise RuntimeError(f"Failed to generate embedding for query: {e}") from e

        # Prepare filters
        where_filter = {}
        if product_category:
            where_filter["product_category"] = product_category

        # Search in vector database
        with self._lock:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=max_results,
                where=where_filter if where_filter else None
            )

        # Process and filter results
        formatted_results = []
        if results and results.get("ids") and len(results["ids"]) > 0:
            ids = results["ids"][0]
            documents = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0]

            for i in range(len(ids)):
                # Convert distance to similarity score (cosine distance to similarity)
                similarity = 1 - distances[i]
                
                if similarity >= min_similarity:
                    formatted_results.append({
                        "id": ids[i],
                        "content": documents[i],
                        "metadata": metadatas[i],
                        "similarity": similarity,
                        "relevance_score": round(similarity * 100, 1)
                    })

        # Sort by similarity (highest first)
        formatted_results.sort(key=lambda x: x["similarity"], reverse=True)
        return formatted_results

    def get_categories(self) -> List[str]:
        """Get all available product categories."""
        with self._lock:
            results = self.collection.get()
            
        categories = set()
        if results and results.get("metadatas"):
            for metadata in results["metadatas"]:
                if metadata and "product_category" in metadata:
                    categories.add(metadata["product_category"])
        
        return sorted(list(categories))

    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        with self._lock:
            results = self.collection.get()
        
        total_docs = len(results.get("ids", []))
        categories = {}
        
        if results and results.get("metadatas"):
            for metadata in results["metadatas"]:
                if metadata and "product_category" in metadata:
                    category = metadata["product_category"]
                    categories[category] = categories.get(category, 0) + 1

        return {
            "total_documents": total_docs,
            "categories": categories,
            "storage_path": self.persist_dir
        }

    def clear_category(self, product_category: str) -> int:
        """Remove all documents from a specific category."""
        with self._lock:
            # Get all documents in the category
            results = self.collection.get(
                where={"product_category": product_category}
            )
            
            if results and results.get("ids"):
                doc_ids = results["ids"]
                self.collection.delete(ids=doc_ids)
                return len(doc_ids)
        
        return 0

    def clear_all(self) -> None:
        """Clear the entire knowledge base."""
        with self._lock:
            self.collection.delete()


# Global knowledge base instance
knowledge_base = None

def get_knowledge_base() -> ProductKnowledgeBase:
    """Get or create the global knowledge base instance."""
    global knowledge_base
    if knowledge_base is None:
        knowledge_base = ProductKnowledgeBase()
    return knowledge_base


def format_knowledge_for_chat(search_results: List[Dict[str, Any]], max_context_length: int = 2000) -> str:
    """
    Format search results for use in chat context with clear source attribution.
    
    Args:
        search_results: Results from knowledge base search
        max_context_length: Maximum length of formatted context
    
    Returns:
        Formatted string for chat context with source indicators
    """
    if not search_results:
        return ""

    context_parts = ["📚 OFFICIAL PRODUCT INFORMATION (from company documentation):"]
    current_length = len(context_parts[0])

    for result in search_results:
        content = result["content"]
        category = result["metadata"].get("product_category", "general")
        filename = result["metadata"].get("filename", "unknown")
        relevance = result["relevance_score"]

        # Create a formatted entry with clear source attribution
        source_header = f"\n\n📋 SOURCE: {category.replace('_', ' ').title()} Documentation"
        source_subheader = f"\n📄 Document: {filename} (Relevance: {relevance}%)"
        source_disclaimer = f"\n⚠️  Note: This is official company product information, not AI-generated content."
        
        entry = f"{source_header}{source_subheader}{source_disclaimer}\n\n{content}"
        
        # Check if adding this entry would exceed the limit
        if current_length + len(entry) > max_context_length:
            # Try to add a truncated version
            available_space = max_context_length - current_length - 200  # Leave buffer for disclaimers
            if available_space > 200:
                truncated_content = content[:available_space] + "..."
                entry = f"{source_header}{source_subheader}{source_disclaimer}\n\n{truncated_content}"
                context_parts.append(entry)
            break
        
        context_parts.append(entry)
        current_length += len(entry)

    # Add final disclaimer
    if len(search_results) > 0:
        final_disclaimer = "\n\n🔍 IMPORTANT: The information above comes directly from our official product documentation. When referencing this information in your response, please clearly indicate it's from official company sources."
        context_parts.append(final_disclaimer)

    return "".join(context_parts)