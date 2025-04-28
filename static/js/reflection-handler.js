
// Reflection handler functionality
document.addEventListener('DOMContentLoaded', function() {
    const submitReflection = document.getElementById('submit-reflection');
    const submitSecondReflection = document.getElementById('submit-second-reflection');
    
    if (submitReflection) {
        submitReflection.addEventListener('click', function() {
            let reflectionText, entryId;
            
            // Get the reflection text with validation
            try {
                const reflectionTextElement = document.getElementById('reflection-text');
                if (!reflectionTextElement) {
                    throw new Error('Reflection text element not found');
                }
                
                reflectionText = reflectionTextElement.value;
                
                // Validate reflection text is not empty
                if (!reflectionText || reflectionText.trim().length === 0) {
                    alert('Please enter your reflection before submitting.');
                    return;
                }
                
                // Safely get the entry ID with multiple fallbacks
                // Try to get from data attribute first
                const entryContainer = this.closest('[data-entry-id]');
                if (entryContainer && entryContainer.dataset && entryContainer.dataset.entryId) {
                    entryId = entryContainer.dataset.entryId;
                    console.log('Using data attribute entry ID:', entryId);
                } else {
                    // Fallback to URL
                    try {
                        const urlParts = window.location.pathname.split('/');
                        entryId = urlParts[urlParts.length - 1];
                        console.log('Using URL-based entry ID fallback:', entryId);
                    } catch (urlErr) {
                        console.error('Error extracting ID from URL:', urlErr);
                        
                        // Final fallback - look for entry ID in the page
                        const hiddenEntryIdField = document.querySelector('input[name="entry_id"]');
                        if (hiddenEntryIdField) {
                            entryId = hiddenEntryIdField.value;
                            console.log('Using hidden field entry ID fallback:', entryId);
                        }
                    }
                }
                
                // If we still don't have a valid entry ID, alert and exit
                if (!entryId) {
                    console.error('Could not determine entry ID');
                    alert('Could not determine which journal entry to save for. Please try refreshing the page.');
                    return;
                }
                
                // Validate entry ID is a number
                if (isNaN(parseInt(entryId))) {
                    console.error('Invalid entry ID format:', entryId);
                    alert('The journal entry ID is invalid. Please try refreshing the page.');
                    return;
                }
                
                // Disable button and show loading state
                submitReflection.disabled = true;
                const originalButtonText = submitReflection.textContent || 'Share Your Reflection';
                submitReflection.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
                
                // Set timeout to re-enable button if server doesn't respond
                const buttonTimeout = setTimeout(() => {
                    if (submitReflection.disabled) {
                        submitReflection.disabled = false;
                        submitReflection.innerHTML = originalButtonText;
                        alert('The server is taking longer than expected. Your reflection might still be processing. Please check after a moment.');
                    }
                }, 15000); // 15 second timeout
                
            } catch (err) {
                console.error('Error preparing to save initial reflection:', err);
                alert('There was a problem preparing to save your reflection. Please try again or refresh the page.');
                return;
            }
            
            // Attempt to send the reflection to the server
            fetch('/journal/save-initial-reflection', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    entry_id: entryId,
                    reflection_text: reflectionText
                })
            })
            .then(response => {
                // Check if response is ok before parsing JSON
                if (!response.ok) {
                    throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Success! Show a brief message before reloading
                    const successMessage = document.createElement('div');
                    successMessage.className = 'alert alert-success mt-3';
                    successMessage.textContent = 'Your reflection has been saved successfully!';
                    
                    const insertAfter = submitReflection.parentNode;
                    if (insertAfter && insertAfter.parentNode) {
                        insertAfter.parentNode.insertBefore(successMessage, insertAfter.nextSibling);
                    }
                    
                    // Reload after a brief delay so the user sees the success message
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    // Server returned an error
                    console.error('Server error:', data.error);
                    alert('Error saving reflection: ' + (data.error || 'Unknown error'));
                    submitReflection.disabled = false;
                    submitReflection.innerHTML = originalButtonText || 'Share Your Reflection';
                }
            })
            .catch(error => {
                // Network or parsing error
                console.error('Error:', error);
                alert('Error saving reflection: ' + error.message);
                submitReflection.disabled = false;
                submitReflection.innerHTML = originalButtonText || 'Share Your Reflection';
            })
            .finally(() => {
                // Clear the timeout regardless of outcome
                clearTimeout(buttonTimeout);
            });
        });
    }
    
    if (submitSecondReflection) {
        submitSecondReflection.addEventListener('click', function() {
            let reflectionText, entryId;
            
            // Get the reflection text with validation
            try {
                const reflectionTextElement = document.getElementById('second-reflection-text');
                if (!reflectionTextElement) {
                    throw new Error('Second reflection text element not found');
                }
                
                reflectionText = reflectionTextElement.value;
                
                // Validate reflection text is not empty
                if (!reflectionText || reflectionText.trim().length === 0) {
                    alert('Please enter your reflection before submitting.');
                    return;
                }
                
                // Safely get the entry ID with multiple fallbacks
                // Try to get from data attribute first
                const entryContainer = this.closest('[data-entry-id]');
                if (entryContainer && entryContainer.dataset && entryContainer.dataset.entryId) {
                    entryId = entryContainer.dataset.entryId;
                    console.log('Using data attribute entry ID:', entryId);
                } else {
                    // Fallback to URL
                    try {
                        const urlParts = window.location.pathname.split('/');
                        entryId = urlParts[urlParts.length - 1];
                        console.log('Using URL-based entry ID fallback:', entryId);
                    } catch (urlErr) {
                        console.error('Error extracting ID from URL:', urlErr);
                        
                        // Final fallback - look for entry ID in the page
                        const hiddenEntryIdField = document.querySelector('input[name="entry_id"]');
                        if (hiddenEntryIdField) {
                            entryId = hiddenEntryIdField.value;
                            console.log('Using hidden field entry ID fallback:', entryId);
                        }
                    }
                }
                
                // If we still don't have a valid entry ID, alert and exit
                if (!entryId) {
                    console.error('Could not determine entry ID');
                    alert('Could not determine which journal entry to save for. Please try refreshing the page.');
                    return;
                }
                
                // Validate entry ID is a number
                if (isNaN(parseInt(entryId))) {
                    console.error('Invalid entry ID format:', entryId);
                    alert('The journal entry ID is invalid. Please try refreshing the page.');
                    return;
                }
                
                // Disable button and show loading state
                submitSecondReflection.disabled = true;
                const originalButtonText = submitSecondReflection.textContent || 'Share Your Response';
                submitSecondReflection.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
                
                // Set timeout to re-enable button if server doesn't respond
                const buttonTimeout = setTimeout(() => {
                    if (submitSecondReflection.disabled) {
                        submitSecondReflection.disabled = false;
                        submitSecondReflection.innerHTML = originalButtonText;
                        alert('The server is taking longer than expected. Your reflection might still be processing. Please check after a moment.');
                    }
                }, 15000); // 15 second timeout
                
            } catch (err) {
                console.error('Error preparing to save second reflection:', err);
                alert('There was a problem preparing to save your reflection. Please try again or refresh the page.');
                return;
            }
            
            // Add a loading message to indicate to the user that their reflection is being processed
            const loadingMessage = document.createElement('div');
            loadingMessage.className = 'alert alert-info mt-3';
            loadingMessage.textContent = 'Processing your reflection. This may take a moment...';
            loadingMessage.id = 'reflection-loading-message';
            
            const insertAfter = submitSecondReflection.parentNode;
            if (insertAfter && insertAfter.parentNode) {
                insertAfter.parentNode.insertBefore(loadingMessage, insertAfter.nextSibling);
            }
            
            // Attempt to send the reflection to the server
            fetch('/journal/save-second-reflection', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    entry_id: entryId,
                    reflection_text: reflectionText
                })
            })
            .then(response => {
                // Check if response is ok before parsing JSON
                if (!response.ok) {
                    throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                // Remove the loading message
                const loadingMsg = document.getElementById('reflection-loading-message');
                if (loadingMsg) {
                    loadingMsg.remove();
                }
                
                if (data.success) {
                    // Success! Show a brief message before reloading
                    const successMessage = document.createElement('div');
                    successMessage.className = 'alert alert-success mt-3';
                    successMessage.textContent = 'Your reflection has been saved successfully! Coach Mira is preparing her final thoughts...';
                    
                    const insertAfter = submitSecondReflection.parentNode;
                    if (insertAfter && insertAfter.parentNode) {
                        insertAfter.parentNode.insertBefore(successMessage, insertAfter.nextSibling);
                    }
                    
                    // Reload after a brief delay so the user sees the success message
                    setTimeout(() => {
                        window.location.reload();
                    }, 1500);
                } else {
                    // Server returned an error
                    console.error('Server error:', data.error);
                    alert('Error saving reflection: ' + (data.error || 'Unknown error'));
                    submitSecondReflection.disabled = false;
                    submitSecondReflection.innerHTML = originalButtonText || 'Share Your Response';
                }
            })
            .catch(error => {
                // Remove the loading message
                const loadingMsg = document.getElementById('reflection-loading-message');
                if (loadingMsg) {
                    loadingMsg.remove();
                }
                
                // Network or parsing error
                console.error('Error:', error);
                alert('Error saving reflection: ' + error.message);
                submitSecondReflection.disabled = false;
                submitSecondReflection.innerHTML = originalButtonText || 'Share Your Response';
            })
            .finally(() => {
                // Clear the timeout regardless of outcome
                clearTimeout(buttonTimeout);
            });
        });
    }
});
