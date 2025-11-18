import os
import sqlite3
from datetime import timedelta
from flask import Flask, redirect, url_for, session, request, render_template, flash, send_from_directory
from authlib.integrations.flask_client import OAuth
from werkzeug.utils import secure_filename
from flask_session import Session

# ---------- Configuration ----------
APP_SECRET = os.environ.get("APP_SECRET", "dev-secret-change-me")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000")  # Replit will set this

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXT = {"png", "jpg", "jpeg", "gif"}

# ---------- App ----------
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = APP_SECRET
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
Session(app)

# ---------- OAuth ----------
oauth = OAuth(app)
if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    pass  # will guard later
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# ---------- Database helpers ----------
DB_PATH = "users.db"

def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        with open('schema.sql', 'r') as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def find_user_by_google_id(gid):
    conn = get_db()
    cur = conn.execute("SELECT * FROM users WHERE google_id = ?", (gid,))
    row = cur.fetchone()
    conn.close()
    return row

def find_user_by_email(email):
    conn = get_db()
    cur = conn.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    conn.close()
    return row

def find_user_by_username(username):
    conn = get_db()
    cur = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    return row

def create_user(google_id, email, email_verified, username=None, profile_image=None):
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO users (google_id, email, email_verified, username, profile_image) VALUES (?,?,?,?,?)",
        (google_id, email, int(email_verified), username, profile_image)
    )
    conn.commit()
    conn.close()
    return cur.lastrowid

def set_username_for_google(google_id, username):
    conn = get_db()
    conn.execute("UPDATE users SET username = ? WHERE google_id = ?", (username, google_id))
    conn.commit()
    conn.close()

def set_profile_image_for_google(google_id, profile_image):
    conn = get_db()
    conn.execute("UPDATE users SET profile_image = ? WHERE google_id = ?", (profile_image, google_id))
    conn.commit()
    conn.close()

# ---------- Utilities ----------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

def current_user():
    if 'user' in session:
        return session['user']
    return None

# ---------- FIXED FOR FLASK 3 ----------
setup_done = False

@app.before_request
def setup():
    global setup_done
    if not setup_done:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        init_db()
        setup_done = True

# ---------- Routes ----------
@app.route('/')
def index():
    user = current_user()
    return render_template("index.html", user=user, dev_name="Shravani")

@app.route('/login')
def login():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return "Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.", 500
    redirect_uri = url_for('authorize', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    token = oauth.google.authorize_access_token()
    userinfo = token.get('userinfo')

    if not userinfo:
        userinfo = oauth.google.parse_id_token(token)
    if not userinfo:
        return "Could not fetch user info from Google.", 400

    google_id = userinfo.get("sub") or userinfo.get("id")
    email = userinfo.get("email")
    email_verified = userinfo.get("email_verified", False)
    picture = userinfo.get("picture")

    if not email or not google_id:
        return "Missing required google account information.", 400

    if not email_verified:
        return render_template("login_required.html", message="Please verify your Google email before using this game.")

    existing = find_user_by_google_id(google_id)
    if not existing:
        create_user(google_id, email, True, None, picture)
        user = find_user_by_google_id(google_id)
    else:
        user = existing

    session.permanent = True
    session['user'] = {
        "id": user["id"],
        "google_id": user["google_id"],
        "email": user["email"],
        "username": user["username"],
        "profile_image": user["profile_image"]
    }

    if not user["username"]:
        return redirect(url_for('choose_username'))

    return redirect(url_for('game'))

@app.route('/choose-username', methods=['GET','POST'])
def choose_username():
    user = current_user()
    if not user:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get("username", "").strip()
        if not username:
            flash("Enter a username.")
            return render_template("choose_username.html", user=user)

        if find_user_by_username(username):
            flash("Username already taken.")
            return render_template("choose_username.html", user=user)

        set_username_for_google(user['google_id'], username)
        session['user']['username'] = username
        return redirect(url_for('profile'))

    return render_template("choose_username.html", user=user)

@app.route('/profile', methods=['GET','POST'])
def profile():
    user = current_user()
    if not user:
        return redirect(url_for('index'))

    if request.method == 'POST':
        if 'profile_image' in request.files:
            f = request.files['profile_image']
            if f and allowed_file(f.filename):
                filename = secure_filename(f.filename)
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                f.save(save_path)
                set_profile_image_for_google(user['google_id'], save_path)
                session['user']['profile_image'] = save_path
                flash("Profile image updated.")
        return redirect(url_for('profile'))

    return render_template("profile.html", user=user, dev_name="Shravani")

@app.route('/game')
def game():
    user = current_user()
    if not user:
        return redirect(url_for('index'))
    if not user.get('username'):
        return redirect(url_for('choose_username'))

    return render_template("game.html", user=user, dev_name="Shravani")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/health')
def health():
    return "OK"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
