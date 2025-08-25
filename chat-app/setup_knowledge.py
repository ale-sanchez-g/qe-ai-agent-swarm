#!/usr/bin/env python3
"""
Setup script for the Chat App Knowledge Base
This script initializes the knowledge base with sample product documents
"""

import os
import sys
from pathlib import Path

# Add the chat-app directory to the Python path
chat_app_dir = Path(__file__).parent
sys.path.insert(0, str(chat_app_dir))

try:
    from product_knowledge import get_knowledge_base
    print("✅ Successfully imported knowledge base modules")
except ImportError as e:
    print(f"❌ Failed to import knowledge base modules: {e}")
    print("Please ensure you have installed the required dependencies:")
    print("pip install chromadb sentence-transformers")
    sys.exit(1)

def setup_knowledge_base():
    """Initialize the knowledge base with sample documents"""
    try:
        print("🚀 Setting up Knowledge Base...")
        
        # Get knowledge base instance
        kb = get_knowledge_base()
        print("✅ Knowledge base instance created")
        
        # Path to sample documents
        sample_dir = chat_app_dir / "sample_knowledge"
        
        if not sample_dir.exists():
            print(f"❌ Sample knowledge directory not found: {sample_dir}")
            return False
        
        # Define categories and their corresponding files
        categories = {
            "home_loans": ["home_loans.md"],
            "car_loans": ["car_loans.md"], 
            "banking_services": ["banking_services.md"]
        }
        
        total_processed = 0
        
        for category, files in categories.items():
            print(f"\n📁 Processing category: {category}")
            
            for filename in files:
                file_path = sample_dir / filename
                
                if not file_path.exists():
                    print(f"  ⚠️  File not found: {filename}")
                    continue
                
                try:
                    # Read file content
                    content = file_path.read_text(encoding='utf-8')
                    
                    # Add to knowledge base
                    doc_id = kb.add_document(
                        content=content,
                        filename=filename,
                        product_category=category,
                        metadata={
                            "source": "sample_data",
                            "setup_script": True,
                            "file_path": str(file_path)
                        }
                    )
                    
                    print(f"  ✅ Added: {filename} -> {doc_id}")
                    total_processed += 1
                    
                except Exception as e:
                    print(f"  ❌ Error processing {filename}: {e}")
        
        # Display statistics
        print(f"\n📊 Setup Complete!")
        print(f"   • Total documents processed: {total_processed}")
        
        # Get and display knowledge base stats
        stats = kb.get_stats()
        print(f"   • Total documents in KB: {stats['total_documents']}")
        print(f"   • Categories: {list(stats['categories'].keys())}")
        print(f"   • Storage location: {stats['storage_path']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False

def test_search():
    """Test the knowledge base search functionality"""
    print("\n🔍 Testing Knowledge Base Search...")
    
    try:
        kb = get_knowledge_base()
        
        # Test queries
        test_queries = [
            "What are the interest rates for home loans?",
            "How do I apply for a car loan?",
            "What banking services do you offer?",
            "Tell me about electric vehicle loans",
            "What is the minimum deposit for a home loan?"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Query: '{query}'")
            
            results = kb.search_knowledge(
                query=query,
                max_results=2,
                min_similarity=0.5
            )
            
            if results:
                for i, result in enumerate(results, 1):
                    category = result['metadata'].get('product_category', 'unknown')
                    filename = result['metadata'].get('filename', 'unknown')
                    relevance = result['relevance_score']
                    
                    print(f"  {i}. [{category}] {filename} - {relevance}% relevant")
                    # Show first 100 characters of content
                    content_preview = result['content'][:100].replace('\n', ' ') + "..."
                    print(f"     Preview: {content_preview}")
            else:
                print("  No results found")
        
        print("\n✅ Search test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Search test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("=" * 60)
    print("🏦 CHAT APP KNOWLEDGE BASE SETUP")
    print("=" * 60)
    
    # Setup knowledge base
    setup_success = setup_knowledge_base()
    
    if setup_success:
        # Test search functionality
        test_search()
        
        print("\n" + "=" * 60)
        print("🎉 SETUP COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("Next steps:")
        print("1. Start the chat app: python app.py")
        print("2. Login to the chat interface")
        print("3. Try asking questions about loans and banking services")
        print("4. Visit /admin/knowledge to manage the knowledge base")
        print("=" * 60)
    else:
        print("\n❌ Setup failed. Please check the error messages above.")

if __name__ == "__main__":
    main()