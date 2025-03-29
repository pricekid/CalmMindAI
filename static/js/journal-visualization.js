// Journal Visualization System
document.addEventListener("DOMContentLoaded", function() {
    // Get the JSON data from the page
    const journalDataElement = document.getElementById('journal-data');
    
    if (journalDataElement) {
        try {
            const journalData = JSON.parse(journalDataElement.textContent);
            
            // Initialize visualization if we have data
            if (journalData && journalData.length > 0) {
                initializeVisualization(journalData);
            }
            
            // Set up the toggle button
            const toggleButton = document.getElementById('toggle-visualization');
            const visualizationContainer = document.getElementById('visualization-container');
            
            if (toggleButton && visualizationContainer) {
                toggleButton.addEventListener('click', function() {
                    visualizationContainer.classList.toggle('d-none');
                    
                    // After removing d-none, add visible class for animation
                    if (!visualizationContainer.classList.contains('d-none')) {
                        // Use setTimeout to allow the browser to process the d-none removal first
                        setTimeout(() => {
                            visualizationContainer.classList.add('visible');
                            toggleButton.innerHTML = '<i class="fas fa-chart-line me-1"></i> Hide Insights';
                        }, 10);
                    } else {
                        visualizationContainer.classList.remove('visible');
                        toggleButton.innerHTML = '<i class="fas fa-chart-line me-1"></i> Show Insights';
                    }
                });
            }
        } catch (error) {
            console.error("Error parsing journal data:", error);
        }
    }
});

// Initialize the visualizations
function initializeVisualization(data) {
    // Sort data by date (oldest to newest) for timeline chart
    const sortedData = [...data].sort((a, b) => 
        new Date(a.created_at) - new Date(b.created_at)
    );
    
    // Create the anxiety timeline chart
    createAnxietyTimelineChart(sortedData);
    
    // Create the word cloud
    createWordCloud(data);
    
    // Update progress indicators
    updateProgressIndicators(data);
}

// Create the anxiety timeline chart
function createAnxietyTimelineChart(data) {
    const ctx = document.getElementById('anxiety-timeline-chart').getContext('2d');
    
    // Extract dates and anxiety levels
    const dates = data.map(entry => {
        const date = new Date(entry.created_at);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });
    
    const anxietyLevels = data.map(entry => entry.anxiety_level);
    const entryIds = data.map(entry => entry.id);
    
    // Create gradient color for chart
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(13, 202, 240, 0.7)');
    gradient.addColorStop(1, 'rgba(13, 202, 240, 0)');
    
    const anxietyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Anxiety Level',
                data: anxietyLevels,
                backgroundColor: gradient,
                borderColor: '#0dcaf0',
                borderWidth: 2,
                pointBackgroundColor: function(context) {
                    const value = context.dataset.data[context.dataIndex];
                    return getAnxietyColor(value);
                },
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 7,
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 10,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#adb5bd',
                        stepSize: 1
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#adb5bd'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(33, 37, 41, 0.9)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: '#0dcaf0',
                    borderWidth: 1,
                    padding: 10,
                    displayColors: false,
                    callbacks: {
                        title: function(tooltipItems) {
                            const index = tooltipItems[0].dataIndex;
                            const entry = data[index];
                            return entry.title;
                        },
                        label: function(context) {
                            const value = context.parsed.y;
                            return `Anxiety Level: ${value}/10`;
                        },
                        afterLabel: function(context) {
                            const index = context.dataIndex;
                            const entry = data[index];
                            const date = new Date(entry.created_at);
                            return `Date: ${date.toLocaleDateString('en-US', { 
                                year: 'numeric', 
                                month: 'long', 
                                day: 'numeric' 
                            })}`;
                        }
                    }
                }
            },
            onClick: function(event, elements) {
                if (elements && elements.length > 0) {
                    const index = elements[0].index;
                    const entryId = entryIds[index];
                    window.location.href = `/journal/${entryId}`;
                }
            }
        }
    });
}

// Create the word cloud visualization
function createWordCloud(data) {
    const containerElement = document.getElementById('word-cloud-container');
    const wordInfoPanel = document.getElementById('word-info-panel');
    
    if (!containerElement) return;
    
    // Clear loading indicator
    containerElement.innerHTML = '';
    
    // Get all content from entries
    const allContent = data.map(entry => entry.content).join(' ');
    
    // Process the text to find common words
    const words = processText(allContent);
    
    // Select the top words (excluding common stop words)
    const topWords = findTopWords(words, 50);
    
    // If no meaningful words found
    if (topWords.length === 0) {
        containerElement.innerHTML = 
            '<div class="text-center py-5">' + 
            '<i class="fas fa-info-circle fa-2x mb-3 text-muted"></i>' + 
            '<h5>Not Enough Data</h5>' + 
            '<p class="text-muted">Write more journal entries to see word patterns</p>' + 
            '</div>';
        return;
    }
    
    // Calculate word sizes and positions
    const containerWidth = containerElement.offsetWidth;
    const containerHeight = containerElement.offsetHeight;
    
    // Map frequency to font sizes (min 14px, max 36px)
    const maxFreq = topWords[0].count;
    const minFreq = topWords[topWords.length - 1].count;
    const fontSizeRange = [14, 36];
    
    // Position words
    for (let i = 0; i < topWords.length; i++) {
        const word = topWords[i];
        
        // Calculate font size based on frequency
        const fontSize = fontSizeRange[0] + 
            ((word.count - minFreq) / (maxFreq - minFreq || 1)) * 
            (fontSizeRange[1] - fontSizeRange[0]);
        
        // Create element for the word
        const wordElement = document.createElement('div');
        wordElement.classList.add('word-cloud-word');
        wordElement.textContent = word.text;
        wordElement.style.fontSize = `${fontSize}px`;
        wordElement.style.color = getWordColor(word.count, minFreq, maxFreq);
        
        // Random position (avoid edges)
        const padding = fontSize;
        const left = (Math.random() * (containerWidth - 2 * padding)) + padding;
        const top = (Math.random() * (containerHeight - 2 * padding)) + padding;
        
        wordElement.style.left = `${left}px`;
        wordElement.style.top = `${top}px`;
        
        // Add click listener to show related entries
        wordElement.addEventListener('click', function() {
            const entries = findEntriesWithWord(data, word.text);
            updateWordInfoPanel(word.text, entries);
        });
        
        containerElement.appendChild(wordElement);
    }
}

// Update the progress indicators
function updateProgressIndicators(data) {
    // Most stats are already calculated in the backend
    // Here we could add additional client-side calculations if needed
}

// Update the word info panel
function updateWordInfoPanel(word, entries) {
    const panel = document.getElementById('word-info-panel');
    if (!panel) return;
    
    // Clear old content and show the panel
    panel.classList.remove('d-none');
    
    // Update header
    const header = panel.querySelector('.card-header');
    if (header) {
        header.innerHTML = `
            <h5 class="mb-0">${word}</h5>
            <small>Found in ${entries.length} entries</small>
        `;
    }
    
    // Create body if it doesn't exist
    let body = panel.querySelector('.card-body');
    if (!body) {
        body = document.createElement('div');
        body.classList.add('card-body');
        panel.appendChild(body);
    } else {
        body.innerHTML = '';
    }
    
    // Add entry links
    if (entries.length > 0) {
        entries.forEach(entry => {
            const entryDate = new Date(entry.created_at);
            const formattedDate = entryDate.toLocaleDateString('en-US', { 
                month: 'short', 
                day: 'numeric',
                year: 'numeric'
            });
            
            const entryLink = document.createElement('a');
            entryLink.href = `/journal/${entry.id}`;
            entryLink.classList.add('entry-link');
            entryLink.innerHTML = `
                <div class="entry-title">${entry.title}</div>
                <div class="entry-date">${formattedDate}</div>
            `;
            
            body.appendChild(entryLink);
        });
    } else {
        body.innerHTML = '<p class="text-center text-muted my-4">No entries found</p>';
    }
}

// Helper function to get anxiety level color
function getAnxietyColor(level) {
    if (level <= 3) {
        return '#28a745'; // Low anxiety - green
    } else if (level <= 6) {
        return '#ffc107'; // Medium anxiety - yellow
    } else {
        return '#dc3545'; // High anxiety - red
    }
}

// Helper function to get word color based on frequency
function getWordColor(count, minFreq, maxFreq) {
    const colors = [
        '#0dcaf0', // bs-info
        '#6f42c1', // bs-purple
        '#20c997', // bs-teal
        '#0d6efd', // bs-primary
        '#6610f2'  // bs-indigo
    ];
    
    // Normalize count to 0-1 range
    const normalized = (count - minFreq) / (maxFreq - minFreq || 1);
    
    // Map to color index
    const colorIndex = Math.floor(normalized * colors.length);
    return colors[Math.min(colorIndex, colors.length - 1)];
}

// Helper function to process text into words
function processText(text) {
    // Common English stop words to filter out
    const stopWords = new Set([
        'a', 'an', 'the', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'shall', 'should', 'can', 
        'could', 'may', 'might', 'must', 'am', 'in', 'on', 'at', 'to', 'for', 'of', 'by', 'with', 
        'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 
        'below', 'from', 'up', 'down', 'this', 'that', 'these', 'those', 'my', 'your', 'his', 
        'her', 'its', 'our', 'their', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 
        'her', 'us', 'them', 'what', 'which', 'who', 'whom', 'whose', 'when', 'where', 'why', 
        'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'some', 'such', 'no', 'nor', 
        'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'ever', 'also', 
        'really', 'very', 'quite', 'get', 'got', 'getting', 'like', 'im', "i'm", "don't", "doesn't",
        "didn't", "isn't", "aren't", "wasn't", "weren't", "haven't", "hasn't", "hadn't", "won't",
        "wouldn't", "cannot", "can't", "mustn't", "let's", "that's", "who's", "what's", "here's",
        "there's", "when's", "where's", "why's", "how's"
    ]);
    
    // Clean text and count word frequencies
    const wordCounts = {};
    
    // Convert to lowercase, remove punctuation, and split into words
    const words = text.toLowerCase()
        .replace(/[^\w\s]/g, '')
        .split(/\s+/)
        .filter(word => word.length > 2 && !stopWords.has(word));
    
    // Count frequencies
    words.forEach(word => {
        wordCounts[word] = (wordCounts[word] || 0) + 1;
    });
    
    return wordCounts;
}

// Helper function to find top words
function findTopWords(wordCounts, limit) {
    // Convert to array of {text, count} objects
    const wordArray = Object.entries(wordCounts)
        .map(([text, count]) => ({ text, count }))
        .filter(word => word.count > 1) // Only include words that appear more than once
        .sort((a, b) => b.count - a.count)
        .slice(0, limit);
    
    return wordArray;
}

// Helper function to find entries containing a specific word
function findEntriesWithWord(data, word) {
    const regex = new RegExp('\\b' + word + '\\b', 'i');
    return data.filter(entry => regex.test(entry.content));
}