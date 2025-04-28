
// Reflection handler functionality
document.addEventListener('DOMContentLoaded', function() {
    const submitReflection = document.getElementById('submit-reflection');
    const submitSecondReflection = document.getElementById('submit-second-reflection');
    
    if (submitReflection) {
        submitReflection.addEventListener('click', function() {
            let reflectionText, entryId;
            
            try {
                reflectionText = document.getElementById('reflection-text').value;
                
                // Safely get the entry ID with fallbacks
                // Try to get from data attribute first
                const entryContainer = this.closest('[data-entry-id]');
                if (entryContainer && entryContainer.dataset && entryContainer.dataset.entryId) {
                    entryId = entryContainer.dataset.entryId;
                } else {
                    // Fallback to URL
                    const urlParts = window.location.pathname.split('/');
                    entryId = urlParts[urlParts.length - 1];
                    console.log('Using URL-based entry ID fallback:', entryId);
                }
                
                // If we still don't have a valid entry ID, alert and exit
                if (!entryId || isNaN(parseInt(entryId))) {
                    console.error('Could not determine entry ID');
                    alert('Could not determine which journal entry to save for. Please try refreshing the page.');
                    return;
                }
                
                submitReflection.disabled = true;
                submitReflection.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
            } catch (err) {
                console.error('Error preparing to save initial reflection:', err);
                alert('There was a problem preparing to save your reflection. Please try again or refresh the page.');
                return;
            }
            
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
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.reload();
                } else {
                    alert('Error saving reflection: ' + data.error);
                    submitReflection.disabled = false;
                    submitReflection.innerHTML = 'Share Your Reflection';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error saving reflection. Please try again.');
                submitReflection.disabled = false;
                submitReflection.innerHTML = 'Share Your Reflection';
            });
        });
    }
    
    if (submitSecondReflection) {
        submitSecondReflection.addEventListener('click', function() {
            let reflectionText, entryId;
            
            try {
                reflectionText = document.getElementById('second-reflection-text').value;
                
                // Safely get the entry ID with fallbacks
                // Try to get from data attribute first
                const entryContainer = this.closest('[data-entry-id]');
                if (entryContainer && entryContainer.dataset && entryContainer.dataset.entryId) {
                    entryId = entryContainer.dataset.entryId;
                } else {
                    // Fallback to URL
                    const urlParts = window.location.pathname.split('/');
                    entryId = urlParts[urlParts.length - 1];
                    console.log('Using URL-based entry ID fallback:', entryId);
                }
                
                // If we still don't have a valid entry ID, alert and exit
                if (!entryId || isNaN(parseInt(entryId))) {
                    console.error('Could not determine entry ID');
                    alert('Could not determine which journal entry to save for. Please try refreshing the page.');
                    return;
                }
                
                submitSecondReflection.disabled = true;
                submitSecondReflection.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
            } catch (err) {
                console.error('Error preparing to save second reflection:', err);
                alert('There was a problem preparing to save your reflection. Please try again or refresh the page.');
                return;
            }
            
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
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.reload();
                } else {
                    alert('Error saving reflection: ' + data.error);
                    submitSecondReflection.disabled = false;
                    submitSecondReflection.innerHTML = 'Share Your Response';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error saving reflection. Please try again.');
                submitSecondReflection.disabled = false;
                submitSecondReflection.innerHTML = 'Share Your Response';
            });
        });
    }
});
