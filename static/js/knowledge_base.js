/**
 * Knowledge Base JavaScript for FlyPig LINE Bot Admin
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize view document functionality
    initViewDocument();
    
    // Initialize delete document functionality
    initDeleteDocument();
    
    // Initialize file upload functionality
    initFileUpload();
});

/**
 * Initialize the view document functionality
 */
function initViewDocument() {
    const viewButtons = document.querySelectorAll('.view-document');
    const documentTitle = document.getElementById('documentTitle');
    const documentContent = document.getElementById('documentContent');
    const downloadBtn = document.getElementById('downloadDocumentBtn');
    
    viewButtons.forEach(button => {
        button.addEventListener('click', function() {
            const docId = this.getAttribute('data-id');
            
            // Show loading state
            documentTitle.textContent = 'Loading...';
            documentContent.textContent = 'Loading document content...';
            
            // Update download button
            downloadBtn.href = `/knowledge_base/download/${docId}`;
            
            // Fetch document data
            fetch(`/knowledge_base/view/${docId}`)
                .then(response => response.json())
                .then(doc => {
                    // Update modal with document data
                    documentTitle.textContent = doc.title;
                    documentContent.textContent = doc.content;
                    
                    // Update download button with title
                    downloadBtn.setAttribute('download', `${doc.title}.txt`);
                })
                .catch(error => {
                    console.error('Error fetching document:', error);
                    documentTitle.textContent = 'Error';
                    documentContent.textContent = 'Failed to load document content. Please try again.';
                });
        });
    });
}

/**
 * Initialize the delete document functionality
 */
function initDeleteDocument() {
    const deleteButtons = document.querySelectorAll('.delete-document');
    const deleteForm = document.getElementById('deleteDocumentForm');
    const deleteDocumentTitle = document.getElementById('deleteDocumentTitle');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const docId = this.getAttribute('data-id');
            const docTitle = this.getAttribute('data-title');
            
            // Set form action and document title
            deleteForm.action = `/knowledge_base/delete/${docId}`;
            deleteDocumentTitle.textContent = docTitle;
        });
    });
}

/**
 * Initialize the file upload functionality
 */
function initFileUpload() {
    const fileInput = document.getElementById('file');
    const titleInput = document.getElementById('title');
    const contentInput = document.getElementById('content');
    
    if (!fileInput || !titleInput || !contentInput) return;
    
    fileInput.addEventListener('change', function() {
        const file = this.files[0];
        if (!file) return;
        
        // Set the title from the filename if empty
        if (titleInput.value.trim() === '') {
            // Remove extension and replace underscores/hyphens with spaces
            const fileName = file.name.replace(/\.[^/.]+$/, "").replace(/[_-]/g, " ");
            // Capitalize first letter of each word
            titleInput.value = fileName.replace(/\b\w/g, l => l.toUpperCase());
        }
        
        // Handle text file preview
        if (file.type === 'text/plain' || 
            file.name.endsWith('.md') || 
            file.name.endsWith('.txt')) {
            
            const reader = new FileReader();
            reader.onload = function(e) {
                contentInput.value = e.target.result;
            };
            reader.readAsText(file);
        } else {
            // For non-text files, show a placeholder message
            contentInput.value = `File content will be processed on upload.\nFile: ${file.name}\nType: ${file.type}\nSize: ${(file.size / 1024).toFixed(2)} KB`;
        }
    });
}

/**
 * Format file size to human-readable format
 * @param {number} bytes - The file size in bytes
 * @returns {string} - Formatted file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Show a preview of the document content
 * @param {string} content - The document content
 * @returns {string} - Truncated content for preview
 */
function getContentPreview(content) {
    const maxPreviewLength = 200;
    
    if (!content) return '';
    
    if (content.length > maxPreviewLength) {
        return content.substring(0, maxPreviewLength) + '...';
    }
    
    return content;
}
