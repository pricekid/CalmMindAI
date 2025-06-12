"""
Static content pages blueprint for terms, privacy, support, and FAQ pages.
"""

from flask import Blueprint, render_template

# Create blueprint for static pages
static_pages_bp = Blueprint('static_pages', __name__)

@static_pages_bp.route('/terms')
def terms():
    """Terms of Service page"""
    return render_template('static/terms.html')

@static_pages_bp.route('/privacy')
def privacy():
    """Privacy Policy page"""
    return render_template('static/privacy.html')

@static_pages_bp.route('/support')
def support():
    """Support page"""
    return render_template('static/support.html')

@static_pages_bp.route('/faq')
def faq():
    """FAQ page"""
    return render_template('static/faq.html')