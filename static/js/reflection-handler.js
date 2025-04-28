
// Reflection handler functionality
document.addEventListener('DOMContentLoaded', function() {
    const submitReflection = document.getElementById('submit-reflection');
    const submitSecondReflection = document.getElementById('submit-second-reflection');
    
    if (submitReflection) {
        submitReflection.addEventListener('click', function() {
            const reflectionText = document.getElementById('reflection-text').value;
            const entryId = this.closest('[data-entry-id]').dataset.entryId;
            
            submitReflection.disabled = true;
            submitReflection.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
            
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
            const reflectionText = document.getElementById('second-reflection-text').value;
            const entryId = this.closest('[data-entry-id]').dataset.entryId;
            
            submitSecondReflection.disabled = true;
            submitSecondReflection.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
            
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
