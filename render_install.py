"""
Render-specific installation page and download functionality.
This module ensures the installation and download pages work properly on Render.
"""
from flask import Blueprint, render_template, send_from_directory, current_app

render_install_bp = Blueprint('render_install', __name__)

@render_install_bp.route('/download')
def download_page():
    """
    Desktop app download page that provides a Spotify-like experience.
    Works consistently on Render deployment.
    """
    return render_template('download.html', title='Download Dear Teddy')

@render_install_bp.route('/download-app')
def download_app():
    """
    Provide a desktop installer for Dear Teddy
    """
    return send_from_directory('static/downloads', 'DearTeddyInstaller.zip', as_attachment=True)

def register_render_install(app):
    """
    Register the Render-specific installation routes with the Flask app.
    """
    app.register_blueprint(render_install_bp)
    current_app.logger.info('Render-specific installation routes registered successfully')