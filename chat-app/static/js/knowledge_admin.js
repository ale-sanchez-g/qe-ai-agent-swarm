/**
 * Knowledge Base Administration Interface
 */

class KnowledgeAdmin {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadStatistics();
        this.loadCategories();
        this.testConnection();
    }

    bindEvents() {
        // File upload events
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const uploadForm = document.getElementById('uploadForm');

        uploadArea.addEventListener('click', () => fileInput.click());
        uploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
        uploadArea.addEventListener('drop', this.handleDrop.bind(this));
        fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        uploadForm.addEventListener('submit', this.handleUpload.bind(this));

        // Category selection
        document.getElementById('categorySelect').addEventListener('change', (e) => {
            if (e.target.value) {
                document.getElementById('categoryInput').value = e.target.value;
            }
        });

        // Folder upload
        document.getElementById('folderUploadForm').addEventListener('submit', this.handleFolderUpload.bind(this));

        // Search
        document.getElementById('searchForm').addEventListener('submit', this.handleSearch.bind(this));
    }

    async loadStatistics() {
        try {
            const response = await fetch('/api/knowledge/stats');
            const data = await response.json();
            
            if (data.success) {
                this.updateStatistics(data.stats);
            } else {
                this.showAlert('Error loading statistics: ' + data.error, 'danger');
            }
        } catch (error) {
            console.error('Error loading statistics:', error);
            this.showAlert('Failed to load statistics', 'danger');
        }
    }

    updateStatistics(stats) {
        document.getElementById('totalDocs').textContent = stats.total_documents;
        document.getElementById('totalCategories').textContent = Object.keys(stats.categories).length;
        
        const categoriesBreakdown = document.getElementById('categoriesBreakdown');
        categoriesBreakdown.innerHTML = '';
        
        for (const [category, count] of Object.entries(stats.categories)) {
            const badge = document.createElement('span');
            badge.className = 'badge bg-secondary me-2 mb-1 category-badge';
            badge.textContent = `${category}: ${count}`;
            categoriesBreakdown.appendChild(badge);
        }

        this.updateCategoriesManagement(stats.categories);
    }

    updateCategoriesManagement(categories) {
        const container = document.getElementById('categoriesManagement');
        container.innerHTML = '';

        for (const [category, count] of Object.entries(categories)) {
            const col = document.createElement('div');
            col.className = 'col-md-4 mb-3';
            col.innerHTML = `
                <div class="card knowledge-card">
                    <div class="card-body">
                        <h6 class="card-title">${category}</h6>
                        <p class="card-text text-muted">${count} documents</p>
                        <button class="btn btn-sm btn-outline-danger" onclick="admin.clearCategory('${category}')">
                            <i class="fas fa-trash me-1"></i>Clear Category
                        </button>
                    </div>
                </div>
            `;
            container.appendChild(col);
        }
    }

    async loadCategories() {
        try {
            const response = await fetch('/api/knowledge/categories');
            const data = await response.json();
            
            if (data.success) {
                this.updateCategorySelects(data.categories);
            }
        } catch (error) {
            console.error('Error loading categories:', error);
        }
    }

    updateCategorySelects(categories) {
        const selects = ['categorySelect', 'searchCategory'];
        
        selects.forEach(selectId => {
            const select = document.getElementById(selectId);
            // Clear existing options (except first one)
            while (select.children.length > 1) {
                select.removeChild(select.lastChild);
            }
            
            categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category;
                option.textContent = category;
                select.appendChild(option);
            });
        });
    }

    handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        e.currentTarget.style.borderColor = '#007bff';
    }

    handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        e.currentTarget.style.borderColor = '#ddd';
        
        const files = Array.from(e.dataTransfer.files);
        this.handleFiles(files);
    }

    handleFileSelect(e) {
        const files = Array.from(e.target.files);
        this.handleFiles(files);
    }

    handleFiles(files) {
        const validFiles = files.filter(file => {
            const extension = file.name.toLowerCase().split('.').pop();
            return ['txt', 'md'].includes(extension) && file.size <= 5 * 1024 * 1024;
        });

        if (validFiles.length !== files.length) {
            this.showAlert('Some files were filtered out. Only .txt and .md files under 5MB are allowed.', 'warning');
        }

        if (validFiles.length > 0) {
            document.getElementById('uploadBtn').disabled = false;
            const uploadArea = document.getElementById('uploadArea');
            uploadArea.innerHTML = `
                <i class="fas fa-check-circle fa-3x text-success mb-3"></i>
                <p class="mb-2">${validFiles.length} file(s) selected</p>
                <small class="text-muted">${validFiles.map(f => f.name).join(', ')}</small>
            `;
        }
    }

    async handleUpload(e) {
        e.preventDefault();
        
        const fileInput = document.getElementById('fileInput');
        const categoryInput = document.getElementById('categoryInput');
        
        if (!fileInput.files.length) {
            this.showAlert('Please select files to upload', 'warning');
            return;
        }

        if (!categoryInput.value.trim()) {
            this.showAlert('Please enter a product category', 'warning');
            return;
        }

        const uploadBtn = document.getElementById('uploadBtn');
        uploadBtn.disabled = true;
        uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Uploading...';

        try {
            const files = Array.from(fileInput.files);
            let successCount = 0;
            let errorCount = 0;

            for (const file of files) {
                const formData = new FormData();
                formData.append('file', file);
                formData.append('category', categoryInput.value.trim());

                const response = await fetch('/api/knowledge/upload', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();
                if (result.success) {
                    successCount++;
                } else {
                    errorCount++;
                    console.error('Upload error for', file.name, ':', result.error);
                }
            }

            if (successCount > 0) {
                this.showAlert(`Successfully uploaded ${successCount} document(s)`, 'success');
                this.loadStatistics();
                this.loadCategories();
            }

            if (errorCount > 0) {
                this.showAlert(`Failed to upload ${errorCount} document(s)`, 'warning');
            }

        } catch (error) {
            console.error('Upload error:', error);
            this.showAlert('Upload failed: ' + error.message, 'danger');
        } finally {
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = '<i class="fas fa-upload me-1"></i>Upload Documents';
            this.resetUploadForm();
        }
    }

    async handleFolderUpload(e) {
        e.preventDefault();
        
        const folderPath = document.getElementById('folderPath').value.trim();
        const category = document.getElementById('folderCategory').value.trim();
        
        if (!folderPath || !category) {
            this.showAlert('Please fill in all fields', 'warning');
            return;
        }

        try {
            const response = await fetch('/api/knowledge/upload_folder', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    folder_path: folderPath,
                    category: category
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showAlert(data.message, 'success');
                this.loadStatistics();
                this.loadCategories();
                
                if (data.results.errors.length > 0) {
                    console.log('Processing errors:', data.results.errors);
                }
            } else {
                this.showAlert('Folder upload failed: ' + data.error, 'danger');
            }
        } catch (error) {
            console.error('Folder upload error:', error);
            this.showAlert('Folder upload failed: ' + error.message, 'danger');
        }
    }

    async handleSearch(e) {
        e.preventDefault();
        
        const query = document.getElementById('searchQuery').value.trim();
        const category = document.getElementById('searchCategory').value;
        const maxResults = document.getElementById('maxResults').value;
        
        if (!query) {
            this.showAlert('Please enter a search query', 'warning');
            return;
        }

        try {
            const requestBody = {
                query: query,
                max_results: parseInt(maxResults),
                min_similarity: 0.7
            };

            if (category) {
                requestBody.category = category;
            }

            const response = await fetch('/api/knowledge/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });

            const data = await response.json();
            
            if (data.success) {
                this.displaySearchResults(data.results, query);
            } else {
                this.showAlert('Search failed: ' + data.error, 'danger');
            }
        } catch (error) {
            console.error('Search error:', error);
            this.showAlert('Search failed: ' + error.message, 'danger');
        }
    }

    displaySearchResults(results, query) {
        const container = document.getElementById('searchResults');
        
        if (results.length === 0) {
            container.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    No relevant documents found for "${query}".
                </div>
            `;
            return;
        }

        let html = `
            <h6 class="mb-3">
                <i class="fas fa-search-plus me-2"></i>
                Found ${results.length} relevant document(s) for "${query}"
            </h6>
        `;

        results.forEach((result, index) => {
            const metadata = result.metadata;
            html += `
                <div class="card mb-3 search-result">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="card-title mb-0">
                                <span class="badge bg-primary me-2">${metadata.product_category}</span>
                                ${metadata.filename}
                            </h6>
                            <span class="badge bg-success">${result.relevance_score}% relevant</span>
                        </div>
                        <p class="card-text">${this.truncateText(result.content, 300)}</p>
                        <small class="text-muted">
                            <i class="fas fa-clock me-1"></i>
                            Added: ${new Date(metadata.added_at * 1000).toLocaleDateString()}
                        </small>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    }

    async clearCategory(category) {
        if (!confirm(`Are you sure you want to delete all documents in the "${category}" category? This action cannot be undone.`)) {
            return;
        }

        try {
            const response = await fetch('/api/knowledge/clear_category', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ category: category })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showAlert(data.message, 'success');
                this.loadStatistics();
                this.loadCategories();
            } else {
                this.showAlert('Failed to clear category: ' + data.error, 'danger');
            }
        } catch (error) {
            console.error('Clear category error:', error);
            this.showAlert('Failed to clear category: ' + error.message, 'danger');
        }
    }

    async testConnection() {
        try {
            const response = await fetch('/api/knowledge/test_connection');
            const data = await response.json();
            
            if (data.success) {
                this.showAlert('Knowledge base connection successful!', 'success');
            } else {
                this.showAlert('Knowledge base connection failed: ' + data.error, 'danger');
            }
        } catch (error) {
            console.error('Connection test error:', error);
            this.showAlert('Knowledge base connection test failed', 'danger');
        }
    }

    resetUploadForm() {
        document.getElementById('fileInput').value = '';
        document.getElementById('categoryInput').value = '';
        document.getElementById('uploadBtn').disabled = true;
        
        const uploadArea = document.getElementById('uploadArea');
        uploadArea.innerHTML = `
            <i class="fas fa-cloud-upload-alt fa-3x text-muted mb-3"></i>
            <p class="mb-2">Drag & drop files here or click to browse</p>
            <small class="text-muted">Supported: .txt, .md files (max 5MB)</small>
        `;
    }

    refreshStats() {
        this.loadStatistics();
        this.loadCategories();
    }

    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    showAlert(message, type) {
        const alertDiv = document.getElementById('statusAlert');
        alertDiv.className = `alert alert-${type}`;
        alertDiv.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check' : type === 'warning' ? 'exclamation-triangle' : 'times'} me-2"></i>
            ${message}
        `;
        alertDiv.classList.remove('d-none');
        
        // Auto-hide success messages
        if (type === 'success') {
            setTimeout(() => {
                alertDiv.classList.add('d-none');
            }, 5000);
        }
    }
}

// Initialize admin interface
const admin = new KnowledgeAdmin();