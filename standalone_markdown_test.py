"""
Standalone test script for the markdown-to-HTML conversion.
"""
import re
import sys
from flask import Flask, render_template_string

# Import the convert_markdown_to_html function directly in this file to avoid circular imports
def convert_markdown_to_html(text):
    """
    Convert markdown formatting to HTML for better display.
    
    Args:
        text: Text containing markdown formatting
        
    Returns:
        Text with markdown converted to HTML
    """
    if not text:
        return ""
    
    # Convert markdown headers (##) to styled headers
    text = re.sub(r'##\s+(.*?)$', r'<h4 class="mt-4 mb-3">\1</h4>', text, flags=re.MULTILINE)
    
    # Convert bold text (**text**) to <strong>
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # Convert bullet points
    text = re.sub(r'^\s*•\s+(.*?)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    
    # Wrap lists in <ul> tags
    text = re.sub(r'(<li>.*?</li>\n)+', r'<ul class="mb-3">\n\g<0></ul>', text, flags=re.DOTALL)
    
    # Convert newlines to breaks for better spacing
    text = text.replace('\n\n', '<br><br>')
    
    return text

app = Flask(__name__)

# Sample response with markdown formatting
markdown_text = """
I've been thinking about what you shared in your journal entry. You mentioned feeling anxious about your upcoming presentation at work.

## Thought Patterns I Notice

**Catastrophizing**: You're imagining the worst possible outcomes ("everyone will laugh at me," "I'll completely freeze up") without considering more realistic scenarios.

**Mind Reading**: You're assuming you know what others will think ("my boss will think I'm incompetent") without evidence.

## CBT Strategies That Might Help

• **Evidence Testing**: Ask yourself what actual evidence you have that your presentation will go poorly. Have you successfully given presentations before?

• **Balanced Thinking**: Instead of focusing only on what might go wrong, try to imagine what could go right or what's most likely to happen.

• **Preparation Without Perfection**: Prepare thoroughly, but accept that perfection isn't required for success.

## Reflection Questions

What specific parts of the presentation make you most nervous? What concrete steps could you take today to feel more prepared?

Remember, feeling nervous about presentations is completely normal - even for experienced speakers.

Warmly,
Mira
"""

@app.route('/')
def test_markdown():
    """Display the converted markdown."""
    html_result = convert_markdown_to_html(markdown_text)
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Markdown Conversion Test</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { padding: 2rem; max-width: 800px; margin: 0 auto; }
            .original { background: #f5f5f5; padding: 1rem; border-radius: 0.5rem; white-space: pre-wrap; }
            .converted { background: #fff; padding: 1rem; border: 1px solid #ddd; border-radius: 0.5rem; }
        </style>
    </head>
    <body>
        <h1 class="mb-4">Markdown Conversion Test</h1>
        
        <h2 class="mb-3">Original Markdown</h2>
        <div class="original mb-4">{{ markdown }}</div>
        
        <h2 class="mb-3">Converted HTML</h2>
        <div class="converted mb-4">{{ html_result|safe }}</div>
        
        <h2 class="mb-3">Raw HTML</h2>
        <pre>{{ html_result|e }}</pre>
    </body>
    </html>
    """, markdown=markdown_text, html_result=html_result)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5001)