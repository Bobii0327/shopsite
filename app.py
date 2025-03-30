
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DB_NAME = 'database.db'

# LINE 設定
LINE_CHANNEL_ID = "2007158321"
LINE_CHANNEL_SECRET = "d9bf13bd12fdcb63bf7bba97241e2581"
LINE_CALLBACK = "https://shopsite-bciv.onrender.com/line_callback"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("DROP TABLE IF EXISTS users")
        c.execute("CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT NOT NULL UNIQUE, password TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price REAL, description TEXT, image TEXT, category TEXT)")
        conn.commit()

@app.route('/')
def index():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT DISTINCT category FROM products")
        categories = c.fetchall()
    return render_template('index.html', categories=categories)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE phone=? AND password=?", (phone, password))
            user = c.fetchone()
            if user:
                session['user_id'] = user[0]
                return redirect(url_for('index'))
            else:
                return "登入失敗"
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users (phone, password) VALUES (?, ?)", (phone, password))
                conn.commit()
                return redirect(url_for('login'))
            except:
                return "電話已存在"
    return render_template('register.html')

@app.route('/line_login')
def line_login():
    return redirect(
        f"https://access.line.me/oauth2/v2.1/authorize?response_type=code"
        f"&client_id={LINE_CHANNEL_ID}"
        f"&redirect_uri={LINE_CALLBACK}"
        f"&state=12345&scope=profile%20openid"
    )

@app.route('/line_callback')
def line_callback():
    code = request.args.get("code")
    token_url = "https://api.line.me/oauth2/v2.1/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": LINE_CALLBACK,
        "client_id": LINE_CHANNEL_ID,
        "client_secret": LINE_CHANNEL_SECRET
    }
    response = requests.post(token_url, headers=headers, data=data)
    token_data = response.json()
    access_token = token_data.get("access_token")

    profile_url = "https://api.line.me/v2/profile"
    headers = {"Authorization": f"Bearer {access_token}"}
    profile_response = requests.get(profile_url, headers=headers)
    profile = profile_response.json()

    session['user_name'] = profile.get("displayName")
    return redirect(url_for("index"))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
