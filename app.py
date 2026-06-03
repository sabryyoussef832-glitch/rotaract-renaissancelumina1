import os
import secrets
import time
from datetime import datetime
from flask import Flask, request, jsonify, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = 'lumina_renaissance_secret_stable_key_2026' # Stable key for session persistence
CORS(app, supports_credentials=True)

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

db = SQLAlchemy(app)

# --- Models ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='member')
    photo_path = db.Column(db.String(255))
    cv_path = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ProjectSupport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100))
    supporter_name = db.Column(db.String(100))
    contact = db.Column(db.String(100))
    help_type = db.Column(db.String(100))
    member_id = db.Column(db.Integer)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

class EventRegistration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_title = db.Column(db.String(200), nullable=False)
    attendee_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    event_date = db.Column(db.String(50))
    location = db.Column(db.String(200))
    time = db.Column(db.String(50))
    ticket_id = db.Column(db.String(50), unique=True)
    status = db.Column(db.String(20), default='Confirmed')
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    member_id = db.Column(db.Integer)

# Initialize database
with app.app_context():
    db.create_all()

# --- Helper Functions ---

def save_file(file, folder):
    if not file:
        return None
    filename = secure_filename(f"{int(time.time())}_{file.filename}")
    path = os.path.join(app.config['UPLOAD_FOLDER'], folder, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    file.save(path)
    return f"uploads/{folder}/{filename}"

# --- Routes ---

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(os.path.join('.', path)):
        return send_from_directory('.', path)
    return send_from_directory('.', 'index.html')

@app.route('/api/signup', methods=['POST'])
def signup():
    try:
        name = request.form.get('name')
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password')
        phone = request.form.get('phone')
        photo = request.files.get('photo')
        cv = request.files.get('cv')

        if not name or not email or not password:
            return jsonify({"error": "Missing required fields"}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered"}), 400

        if not photo:
            return jsonify({"error": "Personal photo is required"}), 400

        password_hash = generate_password_hash(password)
        photo_path = save_file(photo, 'photos')
        cv_path = save_file(cv, 'cvs')

        new_user = User(
            name=name,
            email=email,
            password_hash=password_hash,
            photo_path=photo_path,
            cv_path=cv_path,
            phone=phone
        )
        db.session.add(new_user)
        db.session.commit()

        return jsonify({"success": True, "message": "Account created successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/signin', methods=['POST'])
def signin():
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        password = data.get('password')

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({"error": "Invalid email or password"}), 401

        session['user_id'] = user.id
        user_data = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
        return jsonify({"success": True, "user": user_data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/me', methods=['GET'])
def get_me():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "success": True,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    })

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({"success": True, "message": "Logged out"}), 200

@app.route('/api/account/name', methods=['POST'])
def update_name():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    new_name = data.get('name', '').strip()
    if len(new_name) < 2:
        return jsonify({"error": "Name too short"}), 400
    
    user = User.query.get(user_id)
    user.name = new_name
    db.session.commit()
    
    return jsonify({
        "success": True, 
        "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role}
    })

@app.route('/api/account/password', methods=['POST'])
def update_password():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    current_password = data.get('currentPassword')
    new_password = data.get('newPassword')
    
    user = User.query.get(user_id)
    if not check_password_hash(user.password_hash, current_password):
        return jsonify({"error": "Incorrect current password"}), 401
    
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    return jsonify({"success": True, "message": "Password updated"})

# --- Forgot Password Flows ---

# Temporary storage for verification codes (In production, use Redis or a DB table)
verification_codes = {}

@app.route('/api/forgot-password/send-code', methods=['POST'])
def send_recovery_code():
    data = request.get_json()
    phone = data.get('phone')
    
    if not phone:
        return jsonify({"error": "Phone number is required"}), 400
    
    user = User.query.filter_by(phone=phone).first()
    if not user:
        return jsonify({"error": "No account found with this phone number"}), 404
    
    # Generate a simple 6-digit code
    code = secrets.token_hex(3)[:6].upper()
    verification_codes[phone] = {
        "code": "123456", # Hardcoded for demonstration as requested
        "expires": time.time() + 600 # 10 minutes
    }
    
    print(f"DEBUG: Verification code for {phone} is 123456")
    
    return jsonify({"success": True, "message": "Code sent successfully"}), 200

@app.route('/api/forgot-password/verify-code', methods=['POST'])
def verify_recovery_code():
    data = request.get_json()
    phone = data.get('phone')
    code = data.get('code')
    
    if not phone or not code:
        return jsonify({"error": "Phone and code are required"}), 400
    
    stored = verification_codes.get(phone)
    if not stored:
        return jsonify({"error": "Session expired or invalid"}), 400
    
    if stored['expires'] < time.time():
        del verification_codes[phone]
        return jsonify({"error": "Code expired"}), 400
    
    if code != stored['code']:
        return jsonify({"error": "Invalid verification code"}), 400
    
    return jsonify({"success": True, "message": "Code verified"}), 200

@app.route('/api/forgot-password/reset', methods=['POST'])
def reset_password():
    data = request.get_json()
    phone = data.get('phone')
    code = data.get('code')
    new_password = data.get('newPassword')
    
    if not phone or not code or not new_password:
        return jsonify({"error": "Missing fields"}), 400
    
    stored = verification_codes.get(phone)
    if not stored or stored['code'] != code:
        return jsonify({"error": "Security check failed. Please restart the process."}), 403
    
    user = User.query.filter_by(phone=phone).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    
    # Clean up
    del verification_codes[phone]
    
    return jsonify({"success": True, "message": "Password reset successfully"}), 200

@app.route('/api/project-support', methods=['POST'])
def project_support():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Members only"}), 401
    
    data = request.get_json()
    new_support = ProjectSupport(
        title=data.get('title'),
        category=data.get('category'),
        supporter_name=data.get('supporterName'),
        contact=data.get('contact'),
        help_type=data.get('helpType'),
        member_id=user_id
    )
    db.session.add(new_support)
    db.session.commit()
    return jsonify({"success": True, "message": "Support request saved"}), 201

@app.route('/api/event-registration', methods=['POST'])
def event_registration():
    data = request.get_json()
    ticket_id = f"LUMINA-{secrets.token_hex(3).upper()}"
    user_id = session.get('user_id')
    
    new_reg = EventRegistration(
        event_title=data.get('title'),
        attendee_name=data.get('attendeeName'),
        phone=data.get('phone'),
        email=data.get('email'),
        event_date=data.get('eventDate'),
        location=data.get('location'),
        time=data.get('time'),
        ticket_id=ticket_id,
        member_id=user_id
    )
    db.session.add(new_reg)
    db.session.commit()
    return jsonify({"success": True, "ticketID": ticket_id}), 201

@app.route('/api/admin-dashboard', methods=['GET'])
def admin_dashboard():
    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None
    if not user or user.role != 'admin':
        return jsonify({"error": "Admin access required"}), 403
    
    users = User.query.all()
    projects = ProjectSupport.query.all()
    events = EventRegistration.query.all()
    
    return jsonify({
        "success": True,
        "summary": {
            "users": len(users),
            "projectSupport": len(projects),
            "eventRegistrations": len(events)
        },
        "users": [{"id": u.id, "name": u.name, "email": u.email, "role": u.role} for u in users]
    })

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)
