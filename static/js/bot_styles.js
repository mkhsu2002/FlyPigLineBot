/**
 * Bot Styles JavaScript for FlyPig LINE Bot Admin
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize edit style functionality
    initEditStyle();
    
    // Initialize delete style functionality
    initDeleteStyle();
    
    // Add example templates for different style types
    initStyleTemplates();
});

/**
 * Initialize the edit style functionality
 */
function initEditStyle() {
    const editButtons = document.querySelectorAll('.edit-style');
    const editForm = document.getElementById('editStyleForm');
    
    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            const styleId = this.getAttribute('data-id');
            
            // Set the form action URL
            editForm.action = `/bot_styles/edit/${styleId}`;
            
            // Fetch style data and populate form
            fetch(`/bot_styles/get/${styleId}`)
                .then(response => response.json())
                .then(style => {
                    document.getElementById('edit_name').value = style.name;
                    document.getElementById('edit_prompt').value = style.prompt;
                    document.getElementById('edit_description').value = style.description || '';
                    document.getElementById('edit_is_default').checked = style.is_default;
                })
                .catch(error => {
                    console.error('Error fetching style data:', error);
                    showAlert('Error loading style data. Please try again.', 'danger');
                });
        });
    });
}

/**
 * Initialize the delete style functionality
 */
function initDeleteStyle() {
    const deleteButtons = document.querySelectorAll('.delete-style');
    const deleteForm = document.getElementById('deleteStyleForm');
    const deleteStyleName = document.getElementById('deleteStyleName');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const styleId = this.getAttribute('data-id');
            const styleName = this.getAttribute('data-name');
            
            // Set form action and style name
            deleteForm.action = `/bot_styles/delete/${styleId}`;
            deleteStyleName.textContent = styleName;
        });
    });
}

/**
 * Initialize the style templates functionality
 */
function initStyleTemplates() {
    // Add template buttons to the add style modal
    const addPromptField = document.getElementById('prompt');
    const editPromptField = document.getElementById('edit_prompt');
    
    if (!addPromptField) return;
    
    // Create template buttons container
    const templateContainer = document.createElement('div');
    templateContainer.className = 'mt-2';
    templateContainer.innerHTML = `
        <small class="text-muted">Templates: </small>
        <button type="button" class="btn btn-sm btn-outline-secondary template-btn" data-template="default">Default</button>
        <button type="button" class="btn btn-sm btn-outline-secondary template-btn" data-template="humorous">Humorous</button>
        <button type="button" class="btn btn-sm btn-outline-secondary template-btn" data-template="formal">Formal</button>
        <button type="button" class="btn btn-sm btn-outline-secondary template-btn" data-template="technical">Technical</button>
    `;
    
    // Add container after prompt fields
    addPromptField.parentNode.appendChild(templateContainer.cloneNode(true));
    if (editPromptField) {
        editPromptField.parentNode.appendChild(templateContainer.cloneNode(true));
    }
    
    // Add event listeners to template buttons
    document.querySelectorAll('.template-btn').forEach(button => {
        button.addEventListener('click', function() {
            const template = this.getAttribute('data-template');
            const promptField = this.closest('.modal-body').querySelector('textarea');
            
            promptField.value = getStyleTemplate(template);
        });
    });
}

/**
 * Get a style template by name
 * @param {string} template - Template name
 * @returns {string} - Template text
 */
function getStyleTemplate(template) {
    const templates = {
        default: 
`You are a helpful assistant. You provide clear, concise, and accurate information.
- Respond in a friendly but straightforward manner
- Be helpful without being overly wordy
- When providing instructions, use step-by-step formatting
- When asked a question you don't know the answer to, acknowledge that fact
- Respond in Traditional Chinese when appropriate`,

        humorous: 
`You are a witty and humorous assistant with a playful personality.
- Add light jokes and puns when appropriate
- Use casual, conversational language
- Include pop culture references when relevant
- Keep a positive and upbeat tone throughout conversations
- Don't take yourself too seriously
- Still provide accurate information, but in an entertaining way
- Respond in Traditional Chinese when appropriate`,

        formal: 
`You are a formal and professional assistant.
- Use proper language, grammar, and punctuation
- Avoid colloquialisms, slang, and contractions
- Maintain a respectful and objective tone
- Structure responses in a logical and organized manner
- Use precise terminology appropriate for business or academic contexts
- Provide comprehensive and detailed answers
- Respond in Traditional Chinese when appropriate`,

        technical: 
`You are a technical expert assistant specialized in providing detailed explanations.
- Focus on accuracy and technical depth
- Include relevant technical terms and concepts
- Explain complex topics step-by-step
- Provide code examples or technical specifications when relevant
- Cite sources or standards when applicable
- Use proper formatting for technical content
- Respond in Traditional Chinese when appropriate`
    };
    
    return templates[template] || templates.default;
}
