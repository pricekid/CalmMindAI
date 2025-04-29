"""
Simple test script to verify that our markdown conversion is working properly.
This will run the convert_markdown_to_html function with various test inputs.
"""
import re

def convert_markdown_to_html(text):
    """
    Convert markdown formatting to HTML for better display.
    Also handles legacy formatting for older entries.
    
    Args:
        text: Text containing markdown formatting
        
    Returns:
        Text with markdown converted to HTML
    """
    if not text:
        return ""
    
    # First, standardize newlines to avoid inconsistencies
    text = text.replace('\r\n', '\n')
    
    # Detect if the text has markdown formatting
    has_markdown = "##" in text or "**" in text or "•" in text
    
    # Process sections in order to avoid formatting conflicts
    
    # 1. Convert markdown headers (##) to styled headers
    text = re.sub(r'##\s+(.*?)$', r'<h4 class="mt-4 mb-3">\1</h4>', text, flags=re.MULTILINE)
    
    # 2. Convert bold text (**text**) to <strong>
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # 3. Convert bullet points (both • and - bullets)
    text = re.sub(r'^\s*[•\-]\s+(.*?)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    
    # 4. Wrap lists in <ul> tags, making sure all <li> elements are wrapped
    text = re.sub(r'((<li>.*?</li>\n?)+)', r'<ul class="mb-3">\n\g<0></ul>', text, flags=re.DOTALL)
    
    # If the text doesn't have markdown but has common section headers, format them
    if not has_markdown:
        # Format legacy section headers for entries that don't use markdown
        text = text.replace("Here are a few thought patterns", "<h4 class='mt-4 mb-3'>Thought Patterns</h4>")
        text = text.replace("Here are a few gentle CBT strategies", "<h4 class='mt-4 mb-3'>CBT Strategies</h4>")
        text = text.replace("And a little reflection for today:", "<h4 class='mt-4 mb-3'>Reflection Prompt</h4>")
    
    # 5. Handle paragraph breaks but avoid extra breaks after headers and before lists
    # Replace double newlines with paragraph breaks, but not if preceded by header or followed by list
    text = re.sub(r'(?<!</h4>)\n\n(?!<ul)', '<br><br>', text)
    
    # 6. Remove any remaining excessive newlines around HTML elements
    text = re.sub(r'\n+(<h4|<ul|<li|</ul>)', r'\1', text)
    text = re.sub(r'(</h4>|</ul>|</li>)\n+', r'\1', text)
    
    return text

# Test both markdown-formatted and legacy text
test_markdown = """## Emotional Validation

I notice that you're feeling **overwhelmed** and **anxious** about your situation. It's completely understandable to feel this way when you're facing such challenging circumstances.

## Thought Patterns

• All-or-nothing thinking: "I'm completely failing at everything"
• Catastrophizing: "This situation will never improve"
• Mind reading: Assuming others are judging you negatively

## CBT Strategies

• Practice self-compassion by treating yourself with the same kindness you would offer a friend
• Challenge negative thoughts by looking for evidence that contradicts them
• Break down overwhelming tasks into smaller, manageable steps"""

test_legacy = """Thank you for sharing your thoughts with me today.

I can hear that you're dealing with a lot of stress right now. It's completely natural to feel overwhelmed when multiple challenges arise at once.

Here are a few thought patterns I noticed in your entry:
- You mentioned feeling like you're "not good enough" which might reflect some self-criticism
- There seems to be a tendency to take responsibility for things outside your control
- You expressed worry about what others might think of your decisions

Here are a few gentle CBT strategies that might help:
- Try to notice when critical thoughts arise and ask if you'd judge a friend that harshly
- Consider writing down evidence that contradicts negative beliefs about yourself
- Practice setting boundaries where appropriate to protect your energy

And a little reflection for today: What would you say to a friend facing the same situation you're in right now?

Warmly,
Coach Mira"""

# Test and print results
print("MARKDOWN TEXT CONVERSION RESULT:")
print("=" * 50)
print(convert_markdown_to_html(test_markdown))
print("\n\nLEGACY TEXT CONVERSION RESULT:")
print("=" * 50)
print(convert_markdown_to_html(test_legacy))