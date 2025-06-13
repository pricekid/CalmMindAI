from flask import Blueprint, request, jsonify, current_app
import psycopg2, os
import uuid
import traceback
from werkzeug.security import generate_password_hash

bp = Blueprint('minimal_register', __name__, url_prefix='/minimal-register')

@bp.route('', methods=['POST'])
def register():
    try:
        # Debug: Log request details
        current_app.logger.info(f"Minimal register - Method: {request.method}")
        current_app.logger.info(f"Minimal register - Form data: {request.form}")
        
        # Handle both form and JSON data safely
        json_data = None
        try:
            json_data = request.get_json(silent=True)
        except:
            pass
        current_app.logger.info(f"Minimal register - JSON data: {json_data}")
        
        data = request.form or json_data or {}
        required = ['username','email','password']
        if not all(k in data for k in required):
            missing = [k for k in required if k not in data]
            return jsonify(error=f'Missing fields: {missing}'), 400

        # Debug: Log we're attempting DB connection
        current_app.logger.info("Attempting database connection...")
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        
        try:
            # Generate user ID and hash password
            user_id = str(uuid.uuid4())
            password_hash = generate_password_hash(data['password'])
            
            current_app.logger.info(f"Inserting user with ID: {user_id}")
            
            # Insert into the actual "user" table with required columns
            cur.execute(
                """INSERT INTO "user" (id, username, email, password_hash, created_at, demographics_collected, notifications_enabled, morning_reminder_enabled, evening_reminder_enabled, sms_notifications_enabled, welcome_message_shown) 
                   VALUES (%s, %s, %s, %s, NOW(), false, true, true, true, false, false) 
                   RETURNING id;""",
                (user_id, data['username'], data['email'], password_hash)
            )
            new_id = cur.fetchone()[0]
            conn.commit()
            current_app.logger.info(f"User created successfully with ID: {new_id}")
            return jsonify(success=True, user_id=new_id), 200
        except psycopg2.errors.UniqueViolation as e:
            conn.rollback()
            current_app.logger.warning(f"UniqueViolation: {str(e)}")
            return jsonify(error='Email already registered'), 409
        except Exception as e:
            conn.rollback()
            current_app.logger.error(f"Database error: {str(e)}")
            current_app.logger.error(f"Full traceback: {traceback.format_exc()}")
            return jsonify(error=f'Database error: {str(e)}'), 500
        finally:
            cur.close()
            conn.close()
    except Exception as e:
        current_app.logger.error(f"General error in minimal register: {str(e)}")
        current_app.logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify(error=f'Server error: {str(e)}'), 500