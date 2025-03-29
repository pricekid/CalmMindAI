document.addEventListener('DOMContentLoaded', function() {
    // Get mood data from the server (passed as variables to the template)
    const moodDates = JSON.parse(document.getElementById('mood-dates-data').textContent);
    const moodScores = JSON.parse(document.getElementById('mood-scores-data').textContent);
    
    // Only create the chart if there's data
    if (document.getElementById('moodChart') && moodDates.length > 0) {
        // Format data for Chart.js
        const chartData = {
            labels: moodDates,
            datasets: [{
                label: 'Mood Score (1-10)',
                data: moodScores,
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 2,
                tension: 0.3,
                fill: true
            }]
        };
        
        // Chart configuration
        const config = {
            type: 'line',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        min: 1,
                        max: 10,
                        ticks: {
                            stepSize: 1
                        },
                        title: {
                            display: true,
                            text: 'Mood Score'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            title: function(context) {
                                return 'Date: ' + context[0].label;
                            },
                            label: function(context) {
                                return 'Mood: ' + context.raw + '/10';
                            }
                        }
                    },
                    legend: {
                        display: false
                    }
                }
            }
        };
        
        // Create the chart
        new Chart(document.getElementById('moodChart'), config);
    } else if (document.getElementById('moodChart')) {
        // If no data available, show a message
        document.getElementById('moodChart').style.display = 'none';
        document.getElementById('mood-chart-container').innerHTML += '<p class="text-center text-muted">No mood data available yet. Start logging your mood to see your progress!</p>';
    }
    
    // Mood log slider value display
    const moodSlider = document.getElementById('mood_score');
    const moodValue = document.getElementById('mood-value');
    
    if (moodSlider && moodValue) {
        // Update the displayed value when the slider changes
        moodSlider.addEventListener('input', function() {
            moodValue.textContent = this.value;
            
            // Change color based on mood value
            let color;
            const value = parseInt(this.value);
            
            if (value <= 3) {
                color = 'var(--bs-danger)';
            } else if (value <= 5) {
                color = 'var(--bs-warning)';
            } else if (value <= 7) {
                color = 'var(--bs-info)';
            } else {
                color = 'var(--bs-success)';
            }
            
            moodValue.style.color = color;
        });
        
        // Trigger once to set initial state
        moodSlider.dispatchEvent(new Event('input'));
    }
});
