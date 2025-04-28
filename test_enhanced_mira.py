import logging
import json
from flask import Blueprint, render_template, request, jsonify
from journal_service import analyze_journal_with_gpt

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create a blueprint instead of a Flask app
app = Blueprint('test_enhanced_mira', __name__)

# Sample journal entry for testing
SAMPLE_JOURNAL_ENTRY = """
my partner went away for 10 day. for teh first 2 days she messaged briefly, the finallly she called on the 3rd day. i missed her call but wheni called back she was at home with family and was talking to me, but most of the time i spent listening to her talking to others. her mum then called and she told me she woudl call me back, but she didnt. following day she messaged good mornng and said she was out and about at work. nothing since. how shoudl i feel
"""

# Testing route - with / at the root of the blueprint
@app.route('/', methods=['GET'])
def test_enhanced_mira():
    """
    Test the enhanced Mira responses with emotional intelligence improvements.
    """
    return render_template('test_enhanced_mira.html', 
                          journal_entry=SAMPLE_JOURNAL_ENTRY)

@app.route('/api/test-analysis', methods=['POST'])
def test_analysis():
    """
    API endpoint to test the enhanced Mira analysis.
    """
    try:
        # Get the data from the request
        data = request.get_json()
        journal_text = data.get('journal_text', SAMPLE_JOURNAL_ENTRY)
        anxiety_level = data.get('anxiety_level', 6)
        
        # Call the analysis function
        result = analyze_journal_with_gpt(
            journal_text=journal_text,
            anxiety_level=anxiety_level,
            user_id=0  # Use 0 for testing
        )
        
        # Log the result for debugging
        logger.debug(f"Analysis result: {json.dumps(result, indent=2)}")
        
        # Return the result
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in test analysis: {str(e)}")
        return jsonify({"error": str(e)}), 500

# This file is now used as a blueprint, so we don't need the run code
# Blueprint is registered in app.py with the url_prefix '/enhanced-mira'