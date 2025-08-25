"""
Knowledge Management API for the Chat App
Provides endpoints for managing product knowledge base
"""

import os
import json
from pathlib import Path
from flask import Blueprint, request, jsonify, session, render_template
from werkzeug.utils import secure_filename
from product_knowledge import get_knowledge_base, format_knowledge_for_chat

# Create blueprint for knowledge management
knowledge_bp = Blueprint('knowledge', __name__, url_prefix='/api/knowledge')

# Configuration
UPLOAD_FOLDER = 'knowledge_uploads'
ALLOWED_EXTENSIONS = {'txt', 'md'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def require_auth():
    """Check if user is authenticated."""
    if 'authenticated' not in session or not session['authenticated']:
        return jsonify({'error': 'Authentication required'}), 401
    return None

@knowledge_bp.route('/upload', methods=['POST'])
def upload_document():
    """Upload a single document to the knowledge base."""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get additional parameters
        product_category = request.form.get('category', 'general').strip()
        if not product_category:
            product_category = 'general'
        
        # Validate file
        if not allowed_file(file.filename):
            return jsonify({'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
        
        # Read file content
        content = file.read().decode('utf-8', errors='ignore')
        if not content.strip():
            return jsonify({'error': 'File is empty'}), 400
        
        if len(content.encode('utf-8')) > MAX_FILE_SIZE:
            return jsonify({'error': f'File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB'}), 400
        
        # Add to knowledge base
        kb = get_knowledge_base()
        doc_id = kb.add_document(
            content=content,
            filename=secure_filename(file.filename),
            product_category=product_category,
            metadata={
                'uploaded_by': session.get('user_id', 'unknown'),
                'upload_method': 'web_upload'
            }
        )
        
        return jsonify({
            'success': True,
            'message': 'Document uploaded successfully',
            'document_id': doc_id,
            'category': product_category,
            'filename': file.filename
        })
        
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@knowledge_bp.route('/upload_folder', methods=['POST'])
def upload_folder():
    """Upload multiple documents from a folder path."""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    try:
        data = request.get_json()
        folder_path = data.get('folder_path', '').strip()
        product_category = data.get('category', 'general').strip()
        
        if not folder_path:
            return jsonify({'error': 'Folder path is required'}), 400
        
        if not os.path.exists(folder_path):
            return jsonify({'error': 'Folder does not exist'}), 400
        
        # Process folder
        kb = get_knowledge_base()
        results = kb.add_documents_from_folder(
            folder_path=folder_path,
            product_category=product_category
        )
        
        return jsonify({
            'success': True,
            'message': f'Processed {results["processed"]} documents',
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': f'Folder upload failed: {str(e)}'}), 500

@knowledge_bp.route('/search', methods=['POST'])
def search_knowledge():
    """Search the knowledge base."""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        product_category = data.get('category')  # None means all categories
        max_results = min(data.get('max_results', 5), 20)  # Cap at 20
        min_similarity = max(data.get('min_similarity', 0.2), 0.0)  # Default to 0.2 instead of 0.7
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Search knowledge base
        kb = get_knowledge_base()
        results = kb.search_knowledge(
            query=query,
            product_category=product_category,
            max_results=max_results,
            min_similarity=min_similarity
        )
        
        return jsonify({
            'success': True,
            'query': query,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

@knowledge_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all available product categories."""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    try:
        kb = get_knowledge_base()
        categories = kb.get_categories()
        
        return jsonify({
            'success': True,
            'categories': categories
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get categories: {str(e)}'}), 500

@knowledge_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get knowledge base statistics."""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    try:
        kb = get_knowledge_base()
        stats = kb.get_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get stats: {str(e)}'}), 500

@knowledge_bp.route('/clear_category', methods=['DELETE'])
def clear_category():
    """Clear all documents from a specific category."""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    try:
        data = request.get_json()
        product_category = data.get('category', '').strip()
        
        if not product_category:
            return jsonify({'error': 'Category is required'}), 400
        
        kb = get_knowledge_base()
        deleted_count = kb.clear_category(product_category)
        
        return jsonify({
            'success': True,
            'message': f'Deleted {deleted_count} documents from category "{product_category}"',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to clear category: {str(e)}'}), 500

@knowledge_bp.route('/test_connection', methods=['GET'])
def test_connection():
    """Test knowledge base connection and dependencies."""
    try:
        kb = get_knowledge_base()
        stats = kb.get_stats()
        
        return jsonify({
            'success': True,
            'message': 'Knowledge base is working correctly',
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Knowledge base error: {str(e)}',
            'message': 'Please ensure ChromaDB and sentence-transformers are installed'
        }), 500