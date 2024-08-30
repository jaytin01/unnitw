from flask import Flask, render_template, request, redirect, url_for, session
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

ADMIN_USER = 'admin'
ADMIN_PASSWORD = 'adminpassword'
USER_FILE = 'users.json'
RESET_FILE = 'resetpass.json'

def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def load_resets():
    if os.path.exists(RESET_FILE):
        with open(RESET_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_resets(resets):
    with open(RESET_FILE, 'w') as f:
        json.dump(resets, f, indent=4)

@app.route('/')
def home():
    if 'username' in session:
        if session.get('admin'):
            return redirect(url_for('admin'))
        return render_template('home.html')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = load_users()
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_USER and password == ADMIN_PASSWORD:
            session['admin'] = True
            session['username'] = username
            return redirect(url_for('admin'))
        
        elif username in users and users[username]['password'] == password:
            if users[username].get('approved'):
                session['username'] = username
                return redirect(url_for('home'))
            else:
                return "Your account is pending approval."
        else:
            return "Invalid credentials."

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = load_users()
        username = request.form['username']
        password = request.form['password']
        
        if username in users:
            return "Username already exists!"
        
        users[username] = {'password': password, 'approved': False}
        save_users(users)
        return "Registration successful! Awaiting approval."
    
    return render_template('register.html')

@app.route('/admin')
def admin():
    if 'admin' in session:
        users = load_users()
        pending_users = {u: p for u, p in users.items() if not p.get('approved')}
        resets = load_resets()
        return render_template('approval.html', users=pending_users, resets=resets)
    return redirect(url_for('login'))

@app.route('/approve_user/<username>')
def approve_user(username):
    if 'admin' in session:
        users = load_users()
        if username in users:
            users[username]['approved'] = True
            save_users(users)
        return redirect(url_for('admin'))

@app.route('/reject_user/<username>')
def reject_user(username):
    if 'admin' in session:
        users = load_users()
        if username in users:
            users.pop(username)
            save_users(users)
        return redirect(url_for('admin'))

@app.route('/complete_reset/<email>')
def complete_reset(email):
    if 'admin' in session:
        resets = load_resets()
        if email in resets:
            resets[email]['status'] = 'Completed'
            save_resets(resets)
        return redirect(url_for('admin'))

@app.route('/cancel_reset/<email>')
def cancel_reset(email):
    if 'admin' in session:
        resets = load_resets()
        if email in resets:
            del resets[email]  # Remove the reset request
            save_resets(resets)
        return redirect(url_for('admin'))

@app.route('/reset', methods=['GET', 'POST'])
def reset():
    if request.method == 'POST':
        email = request.form['email']
        new_password = request.form['new_password']

        resets = load_resets()  # Load existing reset requests
        resets[email] = {'new_password': new_password}  # Add new reset request
        save_resets(resets)  # Save updated reset requests

        return "Password reset request received."

    return render_template('reset.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('admin', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
