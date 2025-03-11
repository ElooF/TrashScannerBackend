from flask import Flask, render_template, request, redirect, url_for, session
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin
import os
import re
import time
import secrets  # Added for generating a fallback secret key
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask app
app = Flask(__name__, template_folder='templates')

# Securely fetch or generate SECRET_KEY
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))

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
        email = request.form['email']
        password = request.form['password']
        
        # Authenticate user securely
        if email in users and check_password_hash(users[email]['password'], password):
            user = User(email)
            login_user(user)
            return redirect(url_for('scanner'))
        return 'Invalid credentials, please try again.'
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        if email in users:
            return 'User already exists. Please log in.'

        # Store hashed password
        users[email] = {'password': generate_password_hash(password)}
        user = User(email)
        login_user(user)
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
    return redirect(url_for('login'))

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_trash_recommendation(filename):
    """Generates a waste recommendation based on file name."""
    trash_items = {
        'plastic': "Make a nice Christmas ornament out of this plastic material! Here's a link to get you started: <a href='https://youtu.be/8sbgquJgKzM?si=dRnSyHxqqeDlHDiZ' target='_blank'>Watch here</a>",
        'paper': "Make use of this paper by making it into art! Here's a link to get you started: <a href='https://youtu.be/pOq1ZI0dqg4?si=DtKAOkCG7mevN4Ph' target='_blank'>Watch here</a>",
        'metal': "Use this metal for a DIY project. Here's a link to get you started: <a href='https://youtu.be/-r5-7pxolPE?si=7fioJuyg4XOZehiK' target='_blank'>Watch here</a>",
        'glass': "Use this glass for glass art! Here's a link to get you started: <a href='https://youtube.com/shorts/0bvaugnt728?si=_sI7jqGSdfud4Wri' target='_blank'>Watch here</a>",
        'organic': "Compost this organic material. Here's a link to get you started: <a href='https://youtu.be/gjwZalZGmQA?si=ow8D78-GARMu_gjd' target='_blank'>Watch here</a>",
    }

    filename_lower = filename.lower()
    for item, recommendation in trash_items.items():
        if item in filename_lower:
            return recommendation

    return "Sorry, we couldn't identify the trash type. Please try again."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
