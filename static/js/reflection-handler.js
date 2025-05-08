/**
 * Reflection Handler for Calm Journey
 * Manages the interaction with reflection prompts in the conversation UI
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize reflection handlers
    initReflectionHandlers();
});

function initReflectionHandlers() {
    // Find all reflection input areas
    const reflectionForms = document.querySelectorAll('.reflection-form');
    
    reflectionForms.forEach(form => {
        const submitButton = form.querySelector('.submit-reflection');
        const reflectionInput = form.querySelector('.reflection-input');
        const entryId = form.getAttribute('data-entry-id');
        
        if (submitButton && reflectionInput && entryId) {
            // Add event listener for the submit button
            submitButton.addEventListener('click', function() {
                submitReflection(reflectionInput, entryId);
            });
            
            // Add event listener for Enter key in textarea
            reflectionInput.addEventListener('keydown', function(event) {
                // Check if Enter was pressed without Shift (Shift+Enter creates a new line)
                if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault(); // Prevent default form submission
                    submitButton.click(); // Trigger the submit button click
                }
            });
        }
    });
}

function submitReflection(reflectionInput, entryId) {
    const reflection = reflectionInput.value.trim();
    
    // Validate input
    if (!reflection) {
        showAlert('Please enter your reflection before submitting.', 'warning');
        return;
    }
    
    // Get CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
    
    // Get the specific submit button related to this reflection input
    const form = reflectionInput.closest('.reflection-form');
    const submitButton = form.querySelector('.submit-reflection');
    
    // Show loading indicator for this specific submit button
    if (submitButton) {
        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
    }
    
    // Send the reflection to the server
    fetch(`/journal/${entryId}/save-conversation-reflection`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ reflection: reflection })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Network response was not ok: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Handle successful save
            addUserReflectionBubble(reflection, entryId);
            
            // Hide the specific reflection form that was submitted
            if (form) {
                form.style.display = 'none';
            }
            
            // If there's a followup message, add it
            // Check for either followup_message or followup_text (backward compatibility)
            if (data.followup_message) {
                addMiraFollowupBubble(data.followup_message, entryId);
                console.log("Added Mira followup bubble from followup_message");
            } else if (data.followup_text) {
                addMiraFollowupBubble(data.followup_text, entryId);
                console.log("Added Mira followup bubble from followup_text");
            } else {
                console.log("No followup message found in response:", data);
            }
        } else {
            showAlert(`Error: ${data.message}`, 'danger');
        }
    })
    .catch(error => {
        console.error('Error saving reflection:', error);
        showAlert('There was an error saving your reflection. Please try again.', 'danger');
    })
    .finally(() => {
        // Reset submit button state
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.innerHTML = 'Submit Reflection';
        }
    });
}

function addUserReflectionBubble(reflectionText, entryId) {
    // Create a new reflection bubble
    const chatContainer = document.querySelector('.chat-container');
    
    if (!chatContainer) {
        console.error('Chat container not found');
        return;
    }
    
    // Only check for exact duplication of the current reflection text
    // This allows multiple reflections while preventing duplicates
    const existingReflections = document.querySelectorAll('.chat-message.user-message');
    for (const existingReflection of existingReflections) {
        // Check if this is a reflection with identical content
        const reflectionLabel = existingReflection.querySelector('.chat-info span');
        const reflectionContent = existingReflection.querySelector('.chat-content p');
        if (reflectionLabel && 
            reflectionLabel.textContent.trim() === 'Your reflection' &&
            reflectionContent && 
            reflectionContent.textContent.trim() === reflectionText.trim()) {
            console.log('Identical user reflection already exists - skipping append');
            return; // Skip adding a duplicate bubble
        }
    }
    
    // Get user initial from existing avatar if possible
    let userInitial = 'U';
    const existingUserAvatar = document.querySelector('.chat-avatar-circle span');
    if (existingUserAvatar) {
        userInitial = existingUserAvatar.textContent;
    }
    
    // Create the user reflection bubble
    const userReflectionBubble = document.createElement('div');
    userReflectionBubble.className = 'chat-message user-message mb-4';
    userReflectionBubble.innerHTML = `
        <div class="d-flex">
            <div class="chat-avatar me-3">
                <div class="chat-avatar-circle bg-primary text-white">
                    <span>${userInitial}</span>
                </div>
            </div>
            <div class="chat-bubble user-bubble">
                <div class="chat-content">
                    <p class="mb-0">${reflectionText.replace(/\n/g, '<br>')}</p>
                    <div class="chat-info small text-muted mt-1">
                        <span>Your reflection</span>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add it to the chat container
    chatContainer.appendChild(userReflectionBubble);
    
    // Scroll to the new message
    userReflectionBubble.scrollIntoView({ behavior: 'smooth' });
}

function addMiraFollowupBubble(followupText, entryId) {
    // Create a new Mira response bubble
    const chatContainer = document.querySelector('.chat-container');
    
    if (!chatContainer) {
        console.error('Chat container not found');
        return;
    }
    
    // Ensure we have a valid entry ID
    if (!entryId) {
        // Try to get the entry ID from the page if not provided
        const reflectionForm = document.querySelector('.reflection-form');
        if (reflectionForm) {
            entryId = reflectionForm.getAttribute('data-entry-id');
        }
    }
    
    // Check if the followup message is already displayed (to prevent duplication)
    const existingFollowups = document.querySelectorAll('.chat-message.mira-message');
    let firstMiraMessage = document.querySelector('.chat-message.mira-message');
    let followupCount = 0;
    
    for (const existingFollowup of existingFollowups) {
        // Skip the first Mira message (which is the initial analysis)
        if (existingFollowup === firstMiraMessage) {
            continue;
        }
        followupCount++;
        
        // Check if this is exactly the same followup message
        const messageContent = existingFollowup.querySelector('.chat-content p');
        if (messageContent && messageContent.textContent.trim() === followupText.trim()) {
            console.log('Exact same Mira followup already exists in the chat - skipping append');
            return; // Skip adding a new bubble
        }
    }
    
    // Allow multiple followup messages to create a conversation flow
    // Only check for exact duplicates which is handled above
    
    // Create the Mira followup bubble
    const miraFollowupBubble = document.createElement('div');
    miraFollowupBubble.className = 'chat-message mira-message mb-4';
    miraFollowupBubble.innerHTML = `
        <div class="d-flex">
            <div class="chat-avatar me-3">
                <div class="chat-avatar-circle bg-info text-white">
                    <span>M</span>
                </div>
            </div>
            <div class="chat-bubble mira-bubble">
                <div class="chat-content">
                    <p class="mb-0">${followupText.replace(/\n/g, '<br>')}</p>
                    <div class="chat-controls mt-2">
                        <button class="btn btn-sm btn-outline-info tts-btn" 
                                data-text="${followupText.replace(/"/g, '&quot;')}"
                                title="Listen to this message">
                            <i class="fas fa-volume-up"></i> Listen
                        </button>
                    </div>
                    <div class="chat-info text-end small text-muted mt-2">
                        <span>Coach Mira</span>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Create a new reflection form for continued conversation
    const newReflectionForm = createReflectionFormElement(entryId);
    
    // Add them both to the chat container in the correct order
    // First Mira's followup, then the new reflection form
    chatContainer.appendChild(miraFollowupBubble);
    chatContainer.appendChild(newReflectionForm);
    
    // Scroll to the new message and reflection form
    newReflectionForm.scrollIntoView({ behavior: 'smooth' });
}

function hideReflectionForm() {
    // Find the currently active reflection form and hide it
    // We identify it as the one that contains the submit button that was just clicked
    const submittedForm = document.querySelector('.reflection-form .submit-reflection:disabled')?.closest('.reflection-form');
    if (submittedForm) {
        submittedForm.style.display = 'none';
    }
}

function showReflectionLoading(isLoading) {
    // Show/hide loading indicator
    const submitButton = document.querySelector('.submit-reflection');
    
    if (submitButton) {
        if (isLoading) {
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
        } else {
            submitButton.disabled = false;
            submitButton.innerHTML = 'Submit Reflection';
        }
    }
}

function createReflectionFormElement(entryId) {
    // Get user initial from existing avatar if possible
    let userInitial = 'U';
    const existingUserAvatar = document.querySelector('.chat-avatar-circle span');
    if (existingUserAvatar) {
        userInitial = existingUserAvatar.textContent;
    }
    
    // Create a new reflection form for continued conversation
    const newReflectionFormDiv = document.createElement('div');
    newReflectionFormDiv.className = 'reflection-form';
    newReflectionFormDiv.setAttribute('data-entry-id', entryId);
    newReflectionFormDiv.innerHTML = `
        <div class="chat-message user-reflection-message mb-4">
            <div class="d-flex">
                <div class="chat-avatar me-3">
                    <div class="chat-avatar-circle bg-primary text-white">
                        <span>${userInitial}</span>
                    </div>
                </div>
                <div class="chat-bubble user-bubble">
                    <div class="chat-content">
                        <textarea class="form-control reflection-input" rows="3" 
                                placeholder="Share your thoughts on Mira's reflection prompt..."></textarea>
                        <div class="d-flex justify-content-end mt-2">
                            <button class="btn btn-sm btn-outline-secondary me-2 cancel-reflection">Cancel</button>
                            <button class="btn btn-sm btn-primary submit-reflection">Submit Reflection</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add event listeners to the new form
    const submitButton = newReflectionFormDiv.querySelector('.submit-reflection');
    const reflectionInput = newReflectionFormDiv.querySelector('.reflection-input');
    
    if (submitButton && reflectionInput) {
        // Add event listener for the submit button
        submitButton.addEventListener('click', function() {
            submitReflection(reflectionInput, entryId);
        });
        
        // Add event listener for Enter key in textarea
        reflectionInput.addEventListener('keydown', function(event) {
            // Check if Enter was pressed without Shift (Shift+Enter creates a new line)
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault(); // Prevent default form submission
                submitButton.click(); // Trigger the submit button click
            }
        });
    }
    
    // Focus on the new reflection form
    if (reflectionInput) {
        reflectionInput.focus();
    }
    
    return newReflectionFormDiv;
}

function createNewReflectionForm(chatContainer, entryId) {
    // Create a new reflection form element
    const newReflectionFormDiv = createReflectionFormElement(entryId);
    
    // Add the new form to the container
    chatContainer.appendChild(newReflectionFormDiv);
}

function showAlert(message, type) {
    // Create an alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Find the container to append the alert
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alertDiv.classList.remove('show');
            setTimeout(() => alertDiv.remove(), 150);
        }, 5000);
    }
}