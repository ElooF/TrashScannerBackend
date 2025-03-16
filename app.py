from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
import os
import re
import time
import secrets  # Added for generating a fallback secret key
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta  # Added for session expiration
from google.cloud import vision  # Import Google Vision API
import io
import random
import os

cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
print(f"Credential Path: {cred_path}")

if cred_path is None or not os.path.exists(cred_path):
    print("Error: Service account file not found!")


# Initialize Flask app with correct static folder settings
app = Flask(__name__, template_folder='templates', static_folder='static')

# Securely fetch or generate SECRET_KEY
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))

# Set session lifetime (Auto logout after 30 mins of inactivity)
app.permanent_session_lifetime = timedelta(minutes=30)

# File upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists('static/images'):
    os.makedirs('static/images')  # Ensure static images directory exists

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

            recommendation = get_trash_recommendation(file_path)

            return render_template('scanner.html', recommendation=recommendation, image_url=file_path)

    return render_template('scanner.html', recommendation=None)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()  # Ensure complete session clearing
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_trash_recommendation(image_path):
    """Uses Google Vision AI to analyze the waste image and provide recommendations."""
    client = vision.ImageAnnotatorClient()

    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    
    response = client.label_detection(image=image)
    labels = [label.description.lower() for label in response.label_annotations]

    # Recycling/upcycling ideas with multiple variations
    trash_recommendations = {
        'plastic': [
            "Make a nice Christmas ornament out of this plastic material!<br><a href='https://youtu.be/8sbgquJgKzM' target='_blank'>Watch here</a>",
            "Cut this plastic into strips to create eco-friendly gift ribbons.<br><a href='https://youtube.com/shorts/qLZzTd2n9xI?si=-fzxUyJRCGWGQgZo' target='_blank'>Watch here</a>",
            "Use plastic bottles to make vertical gardens for your home.<br><a href='https://youtu.be/bNxcJMBJEiw?si=Ua1e6qPcTRegWhJ0' target='_blank'>Watch here</a>"
        ],
        'paper': [
            "Make use of this paper by making it into art!<br><a href='https://youtu.be/pOq1ZI0dqg4' target='_blank'>Watch here</a>",
            "Recycle paper into handmade notebooks.<br><a href='https://youtu.be/T5RInAQ9Rjw?si=GEgRVd7KhWSYVL4s' target='_blank'>Watch here</a> ",
            "Use shredded paper for composting in your garden.<br><a href='https://youtu.be/1VNSvkZ_D_c?si=TZn5KSL2h_6M9jSb' target='_blank'>Watch here</a> "
        ],
        'metal': [
            "Use this metal for a DIY project.<br><a href='https://youtu.be/-r5-7pxolPE' target='_blank'>Watch here</a>",
            "Turn old metal into creative wall decor.<br><a href='https://youtube.com/shorts/uE4aUCyGqmw?si=XJvj27hAmeKo-ubL' target='_blank'>Watch here</a>",
            "Recycle metal cans into candle holders or planters.<br><a href='https://youtu.be/GnFH9fLz9uE?si=8pucCQzQYbaAkYfA' target='_blank'>Watch here</a>"
        ],
        'glass': [

            "Use this glass for glass art!<br><a href='https://youtube.com/shorts/0bvaugnt728' target='_blank'>Watch here</a>",
            "Turn empty glass jars into stylish lamps.<br><a href='https://youtu.be/_OJ6Hz5vFNY?si=b4SX9KCeZLzowpK5' target='_blank'>Watch here</a>",
            "Crushed glass can be used in mosaic artwork.<br><a href='https://youtube.com/shorts/0vKQ83UFF78?si=ZwDU8vTM6yY3mXZC' target='_blank'>Watch here</a>"
        ],
        'organic': [
            "Compost this organic material.<br><a href='https://youtu.be/gjwZalZGmQA' target='_blank'>Watch here</a>",
            "Use fruit peels for homemade natural cleaners.<br><a href='https://youtube.com/shorts/XqUH9oAZJFw?si=w2_BA9wdUC1W87Gt' target='_blank'>Watch here</a>",
            "Turn coffee grounds into a natural fertilizer for plants.<br><a href='https://youtu.be/U8WeMOuBOs0?si=oQlMxdD2fak9SH3E' target='_blank'>Watch here</a>"
        ],
    }

    for item, recommendations in trash_recommendations.items():
        if item in labels:
            return random.choice(recommendations)  # Return a random recommendation from the list
    
    return "Sorry, we couldn't identify the trash type. Please try again."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
