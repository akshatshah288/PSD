from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "d8c1e10d2c1f853a3d96bcacac88af0c"

login_manager = LoginManager(app)
login_manager.login_view = "login"

# User model
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return User(user[0], user[1])
    return None

# Database setup
def init_db():
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)"
    )
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS books (id INTEGER PRIMARY KEY, title TEXT, author TEXT, description TEXT, pdf_link TEXT)"
    )
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        conn = sqlite3.connect("app.db")
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username already exists. Please choose a different one.", "danger")
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect("app.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user[1], password):
            login_user(User(user[0], username))
            session['username'] = username
            return redirect(url_for('dashboard'))
        flash("Invalid username or password.", "danger")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("SELECT title, author, description, pdf_link FROM books")
    books = cursor.fetchall()
    conn.close()
    return render_template('dashboard.html', books=books, username=current_user.username)

@app.route('/download/<book_id>')
@login_required
def download(book_id):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("SELECT pdf_link FROM books WHERE id = ?", (book_id,))
    book = cursor.fetchone()
    conn.close()
    if book:
        return redirect(book[0])
    flash("Book not found.", "danger")
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
