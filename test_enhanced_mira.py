import os
import sys
from openai_service import generate_journaling_coach_response

# Test class to simulate a journal entry
class TestJournalEntry:
    def __init__(self, content, anxiety_level, title):
        self.content = content
        self.anxiety_level = anxiety_level
        self.title = title

# Sample journal entry from the relationship example
test_entry = TestJournalEntry(
    content="my partner went away for 10 day. for teh first 2 days she messaged briefly, the finallly she called on the 3rd day. i missed her call but wheni called back she was at home with family and was talking to me, but most of the time i spent listening to her talking to others. her mum then called and she told me she woudl call me back, but she didnt. following day she messaged good mornng and said she was out and about at work. nothing since. how shoudl i feel",
    anxiety_level=6,
    title="Relationship Issues"
)

# Generate response using the enhanced prompt
response = generate_journaling_coach_response(test_entry)

# Print the response for testing
print("\n==== ENHANCED MIRA RESPONSE ====\n")
print(response)
print("\n==== END OF RESPONSE ====\n")