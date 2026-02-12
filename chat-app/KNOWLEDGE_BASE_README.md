# Long-Term Memory Knowledge Base

This feature adds long-term memory capabilities to the chat application, allowing it to store and retrieve product information to provide more accurate and contextual responses about your business offerings.

## Overview

The knowledge base system uses:
- **ChromaDB**: Vector database for storing document embeddings
- **Sentence Transformers**: For creating semantic embeddings of documents
- **Semantic Search**: To find relevant information based on user queries

## Features

### 🧠 Smart Knowledge Retrieval
- Automatically searches knowledge base for relevant information when users ask questions
- Integrates search results into AI responses for accurate, product-specific answers
- Supports multiple product categories (home loans, car loans, banking services, etc.)

### 📁 Document Management
- Upload individual documents (.txt, .md files)
- Bulk upload from folders
- Categorize documents by product type
- Version control and deduplication

### 🔍 Advanced Search
- Semantic search (understands meaning, not just keywords)
- Category filtering
- Similarity scoring and relevance ranking
- Real-time search testing interface

### 🎛️ Administration Interface
- Web-based knowledge management
- Upload and organize documents
- View statistics and analytics
- Test search functionality
- Category management

## Setup Instructions

### 1. Install Dependencies

```bash
# Install required Python packages
pip install chromadb sentence-transformers
```

### 2. Initialize Knowledge Base

```bash
# Run the setup script to populate with sample data
cd chat-app
python setup_knowledge.py
```

This will create sample documents for:
- **Home Loans**: Fixed rate, variable rate, first home buyer loans
- **Car Loans**: New, used, and electric vehicle loans  
- **Banking Services**: Transaction accounts, savings, credit cards, personal loans

### 3. Start the Application

```bash
python app.py
```

### 4. Access Knowledge Admin

1. Login to the chat interface
2. Click the Settings dropdown (gear icon)
3. Select "Knowledge Base Admin"
4. Or go directly to: `http://localhost:5000/admin/knowledge`

## Usage Guide

### For End Users (Chat Interface)

The knowledge base works automatically in the background:

1. **Ask Product Questions**: 
   - "What are your home loan rates?"
   - "How do I apply for a car loan?"
   - "What banking services do you offer?"

2. **Get Accurate Responses**: 
   - The AI will search the knowledge base
   - Relevant product information is included in responses
   - Answers are specific to your actual products and services

3. **See Enhanced Context**:
   - Responses include specific rates, terms, and features
   - Information is always up-to-date with your documents
   - AI cites relevant product categories when appropriate

### For Administrators (Knowledge Management)

#### Upload Documents

1. **Single File Upload**:
   - Drag and drop .txt or .md files
   - Specify product category (e.g., "home_loans", "insurance")
   - Files are automatically processed and indexed

2. **Bulk Folder Upload**:
   - Specify a folder path containing multiple documents
   - All .txt and .md files are processed automatically
   - Assign a category to all files in the folder

#### Organize Content

1. **Categories**: Use descriptive names with underscores
   - `home_loans` - All home loan products and information
   - `car_loans` - Vehicle financing options
   - `banking_services` - Everyday banking products
   - `insurance` - Insurance products and coverage
   - `investment` - Investment and wealth management

2. **File Naming**: Use descriptive filenames
   - `home_loan_rates_2024.md`
   - `car_loan_application_process.txt`
   - `savings_account_features.md`

#### Test and Validate

1. **Search Testing**:
   - Use the built-in search interface
   - Try various customer questions
   - Check relevance scores and results
   - Verify AI responses include correct information

2. **Monitor Performance**:
   - View statistics dashboard
   - Check document counts per category
   - Monitor search success rates

## API Endpoints

The knowledge base provides REST API endpoints:

### Document Management
- `POST /api/knowledge/upload` - Upload single document
- `POST /api/knowledge/upload_folder` - Bulk upload from folder
- `DELETE /api/knowledge/clear_category` - Remove all docs from category

### Search and Retrieval
- `POST /api/knowledge/search` - Search knowledge base
- `GET /api/knowledge/categories` - List all categories
- `GET /api/knowledge/stats` - Get statistics

### System
- `GET /api/knowledge/test_connection` - Test knowledge base connectivity

## File Formats

### Supported Formats
- **Markdown (.md)**: Recommended for structured content
- **Text (.txt)**: Plain text documents

### Content Guidelines

1. **Structure**: Use clear headings and sections
2. **Information**: Include specific details (rates, terms, requirements)
3. **Updates**: Keep documents current with latest product information
4. **Consistency**: Use consistent terminology across documents

### Example Document Structure

```markdown
# Product Name

## Overview
Brief description of the product or service

## Features
- Feature 1: Description
- Feature 2: Description

## Rates and Terms
- Interest Rate: X.XX% p.a.
- Loan Term: X to X years
- Minimum Amount: $X,XXX

## Eligibility
- Requirement 1
- Requirement 2

## Application Process
1. Step 1
2. Step 2
3. Step 3

## Contact Information
- Phone: 1800-XXX-XXX
- Email: product@company.com
```

## Technical Details

### Vector Storage
- **Database**: ChromaDB (persistent storage)
- **Embeddings**: all-MiniLM-L6-v2 model (384 dimensions)
- **Storage**: Local filesystem (`knowledge_base/` directory)

### Search Algorithm
- **Similarity**: Cosine similarity
- **Threshold**: 0.7 minimum similarity (configurable)
- **Results**: Top 3-5 most relevant documents
- **Context**: 1500 character limit for AI context

### Performance
- **Indexing**: Automatic when documents are added
- **Search Speed**: Sub-second response times
- **Memory**: ~50MB for 1000 documents
- **Scalability**: Handles thousands of documents efficiently

## Troubleshooting

### Common Issues

1. **Import Errors**:
   ```bash
   pip install chromadb sentence-transformers
   ```

2. **Slow First Search**:
   - Model downloads on first use (normal)
   - Subsequent searches are fast

3. **No Search Results**:
   - Check similarity threshold (try lowering to 0.5)
   - Verify documents are properly categorized
   - Test with simpler queries

4. **Memory Issues**:
   - Reduce max_results in search
   - Use shorter documents
   - Clear unused categories

### Debug Steps

1. **Test Connection**:
   ```python
   from product_knowledge import get_knowledge_base
   kb = get_knowledge_base()
   print(kb.get_stats())
   ```

2. **Manual Search**:
   ```python
   results = kb.search_knowledge("test query", max_results=1)
   print(results)
   ```

3. **Check Logs**: Look for knowledge base errors in app logs

## Security Considerations

- **Access Control**: Knowledge admin requires authentication
- **File Validation**: Only .txt and .md files accepted
- **Content Filtering**: No executable content allowed
- **Size Limits**: 5MB per file maximum
- **Path Traversal**: File paths are sanitized

## Future Enhancements

- **Document Versioning**: Track document changes over time
- **Analytics**: Search query analytics and popular topics
- **Auto-Update**: Automatic document refresh from external sources
- **Multi-Language**: Support for multiple language documents
- **Rich Media**: Support for images and structured data

## Support

For technical issues or questions:
1. Check the troubleshooting section above
2. Review application logs for error messages
3. Test knowledge base connectivity
4. Verify document formatting and content

---

*This knowledge base feature enhances your chat application with intelligent, context-aware responses based on your actual product information.*