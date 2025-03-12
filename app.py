from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
import os
import re
import time
import secrets  # Added for generating a fallback secret key
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta  # Added for session expiration

# Initialize Flask app
app = Flask(__name__, template_folder='templates')

# Securely fetch or generate SECRET_KEY
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))

# Set session lifetime (Auto logout after 30 mins of inactivity)
app.permanent_session_lifetime = timedelta(minutes=30)

# File upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect unauthorized users to login

# Dummy user storage (simulating a simple database)
users = {
    'wastewizai1@gmail.com': {'password': generate_password_hash('password123')}
}

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, email):
        self.id = email

# Load user function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id)
    return None

@app.route('/')
@login_required
def home():
    return redirect(url_for('scanner'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password'].strip()

        if not email or not password:
            flash("Email and password cannot be empty.", "danger")
            return redirect(url_for('login'))

        # Authenticate user securely
        if email in users and check_password_hash(users[email]['password'], password):
            user = User(email)
            login_user(user)
            session.permanent = True  # Keep session alive based on session lifetime
            flash("Login successful!", "success")
            return redirect(url_for('scanner'))

        flash("Invalid credentials, please try again.", "danger")
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password'].strip()

        if not email or not password:
            flash("Email and password cannot be empty.", "danger")
            return redirect(url_for('register'))

        if email in users:
            flash("User already exists. Please log in.", "warning")
            return redirect(url_for('login'))

        # Store hashed password
        users[email] = {'password': generate_password_hash(password)}
        user = User(email)
        login_user(user)
        session.permanent = True
        flash("Registration successful!", "success")
        return redirect(url_for('scanner'))

    return render_template('register.html')

@app.route('/scanner', methods=['GET', 'POST'])
@login_required
def scanner():
    if request.method == 'POST':
        file = request.files['trash_image']
        
        if file and allowed_file(file.filename):
            # Secure filename and add timestamp to avoid overwriting
            filename = secure_filename(file.filename)
            filename = f"{int(time.time())}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            recommendation = get_trash_recommendation(filename)

            return render_template('scanner.html', recommendation=recommendation, image_url=file_path)

    return render_template('scanner.html', recommendation=None)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()  # Ensure complete session clearing
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# Navbar Route
@app.route('/navbar')
def navbar():
    return render_template('navbar.html')

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_trash_recommendation(filename):
    """Generates a waste recommendation with step-by-step instructions and video links."""
    trash_items = {
        'plastic': "Make a nice Christmas ornament out of this plastic material!<br><ul><li>Rinse the plastic.</li><li>Cut into desired pieces.</li><li>Assemble into an ornament.</li><li>Decorate with paint or stickers.</li></ul><a href='https://youtu.be/8sbgquJgKzM' target='_blank'>Watch here</a>",
        'paper': "Make use of this paper by making it into art!<br><ul><li>Collect and sort waste paper.</li><li>Cut or fold into shapes.</li><li>Use glue and colors to create crafts.</li></ul><a href='https://youtu.be/pOq1ZI0dqg4' target='_blank'>Watch here</a>",
        'metal': "Use this metal for a DIY project.<br><ul><li>Clean the metal.</li><li>Cut or shape as needed.</li><li>Assemble with welding or glue.</li></ul><a href='https://youtu.be/-r5-7pxolPE' target='_blank'>Watch here</a>",
        'glass': "Use this glass for glass art!<br><ul><li>Clean the glass thoroughly.</li><li>Sketch a design.</li><li>Paint or decorate.</li></ul><a href='https://youtube.com/shorts/0bvaugnt728' target='_blank'>Watch here</a>",
        'organic': "Compost this organic material.<br><ul><li>Gather organic waste.</li><li>Place in a compost bin.</li><li>Turn compost regularly.</li></ul><a href='https://youtu.be/gjwZalZGmQA' target='_blank'>Watch here</a>",
    }

    filename_lower = filename.lower()
    for item, recommendation in trash_items.items():
        if item in filename_lower:
            return recommendation

    return "Sorry, we couldn't identify the trash type. Please try again."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)  # Added debug mode for easier debugging
