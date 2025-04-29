#!/usr/bin/env python
"""
Script to fix duplicate headers in journal_entry.html
This addresses the issue where headers like "Thought Patterns" and "Suggested Strategies"
appear twice when both the markdown content and the template have headers.
"""

import re

# Define the replacements to make
replacements = [
    # "Suggested Strategies" headers in all sections
    (
        r'(<div class="strategies-section mb-4">\n\s+)<h5 class="mb-3">Suggested Strategies</h5>',
        r'\1{% if not coach_response or "Suggested Strategies" not in coach_response %}\n                                            <h5 class="mb-3">Suggested Strategies</h5>\n                                            {% endif %}'
    ),
    
    # "Thought Patterns" headers in all sections
    (
        r'(<div class="thought-patterns-section mb-4">\n\s+)<h5 class="mb-3">Thought Patterns</h5>',
        r'\1{% if not coach_response or "Thought Patterns" not in coach_response %}\n                                            <h5 class="mb-3">Thought Patterns</h5>\n                                            {% endif %}'
    ),
    
    # Additional "Thought Patterns" headers in different HTML structures (lines 518, 637, 1783)
    (
        r'(<div class="distortions mb-4">\n\s+)<h5 class="mt-4 mb-3">Thought Patterns</h5>',
        r'\1{% if not coach_response or "Thought Patterns" not in coach_response %}\n                                        <h5 class="mt-4 mb-3">Thought Patterns</h5>\n                                        {% endif %}'
    )
]

# Read in the file
with open('templates/journal_entry.html', 'r') as file:
    filedata = file.read()

# Simpler approach: fix all occurrences of each pattern
for pattern, replacement in replacements:
    # Replace all occurrences of the pattern
    filedata = re.sub(pattern, replacement, filedata)

# Write the updated file
with open('templates/journal_entry.html', 'w') as file:
    file.write(filedata)

print("Successfully updated templates/journal_entry.html with duplicate header fixes")