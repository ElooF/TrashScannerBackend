from flask import Flask, render_template, request, redirect, url_for, session
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin
import os
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__, template_folder='templates')
app.secret_key = 'your_secret_key'

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)

# Dummy user storage
users = {
    'test@example.com': {'password': 'password123'},
}

# Allowed file extensions for images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, email):
        self.id = email  # Use the email as the user ID

    def is_authenticated(self):
        return True  # Always return True for simplicity (customize if needed)

# Load user function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id)  # Return a User object instead of just a dictionary
    return None

@app.route('/')
@login_required
def home():
    return redirect(url_for('scanner'))  # Redirect to scanner after login

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check credentials
        if email in users and users[email]['password'] == password:
            user = User(email)  # Create User object, not a dictionary
            login_user(user)  # Log in the user
            return redirect(url_for('scanner'))  # Redirect to the scanner page
        else:
            return 'Invalid credentials, please try again.'
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Store user credentials in the dictionary (replace with database if needed)
        users[email] = {'password': password}
        user = User(email)  # Create User object
        login_user(user)  # Log in the new user
        return redirect(url_for('scanner'))  # Redirect to the scanner page

    return render_template('register.html')

@app.route('/scanner', methods=['GET', 'POST'])
@login_required
def scanner():
    if request.method == 'POST':
        file = request.files['trash_image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join('uploads', filename)
            file.save(file_path)

            # Get recommendation based on the uploaded image file
            recommendation = get_trash_recommendation(filename)

            return render_template('scanner.html', recommendation=recommendation, image_url=file_path)

    return render_template('scanner.html', recommendation=None)

@app.route('/logout')
@login_required
def logout():
    logout_user()  # Log out the user
    return redirect(url_for('login'))  # Redirect to login page

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_trash_recommendation(filename):
    """Simple rule-based trash recommendation based on file name."""
    trash_items = {
        'plastic': "Make a nice Christmas ornament out of this plastic material!",
        'paper': "Make use of this paper by making it into art! Here's a link to get you started: https://youtu.be/pOq1ZI0dqg4?si=DtKAOkCG7mevN4Ph",
        'metal': "Use this metal for a DIY project.",
        'glass': "Use this glass for a glass art!",
        'organic': "Compost this organic material.",
    }

    filename_lower = filename.lower()
    for item, recommendation in trash_items.items():
        if item in filename_lower:
            return recommendation

    return "Sorry, we couldn't identify the trash type. Please try again."

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')  # Ensure the uploads folder exists

    app.run(host='0.0.0.0', port=8000)  # Bind to all available network interfaces
