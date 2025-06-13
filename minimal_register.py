from flask import Blueprint, request, jsonify, current_app
import psycopg2, os
import uuid
from werkzeug.security import generate_password_hash

bp = Blueprint('minimal_register', __name__, url_prefix='/minimal-register')

@bp.route('', methods=['POST'])
def register():
    data = request.form or request.get_json() or {}
    required = ['username','email','password']
    if not all(k in data for k in required):
        return jsonify(error='Missing field'), 400

    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    try:
        # Generate user ID and hash password
        user_id = str(uuid.uuid4())
        password_hash = generate_password_hash(data['password'])
        
        # Insert into the actual "user" table with required columns
        cur.execute(
            """INSERT INTO "user" (id, username, email, password_hash, created_at, demographics_collected, notifications_enabled, morning_reminder_enabled, evening_reminder_enabled, sms_notifications_enabled, welcome_message_shown) 
               VALUES (%s, %s, %s, %s, NOW(), false, true, true, true, false, false) 
               RETURNING id;""",
            (user_id, data['username'], data['email'], password_hash)
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        return jsonify(success=True, user_id=new_id), 200
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return jsonify(error='Email already registered'), 409
    except Exception as e:
        conn.rollback()
        return jsonify(error=str(e)), 500
    finally:
        cur.close()
        conn.close()