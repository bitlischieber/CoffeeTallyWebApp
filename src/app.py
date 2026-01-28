from flask import Flask, render_template, request, redirect, session
import hashlib
from datetime import datetime, timezone
from token_handler import validate_token, get_username_from_token, create_token
from db_handler import get_user_data, authenticate_user, update_user_data, change_password

app = Flask(__name__, template_folder='html', static_folder='html', static_url_path='/static')
app.secret_key = 'your-secret-key-here'  # Change to a secure key in production


def format_datetime(dt):
    """Format datetime to UTC SQL format (YYYY-MM-DD HH:MM:SS)."""
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except:
            return dt
    if isinstance(dt, datetime):
        # Convert to UTC if naive datetime
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return str(dt)


# ==================== INDEX & MAIN ROUTES ====================

@app.route('/')
def route_index():
    token = session.get('token')
    if token and get_username_from_token(token):
        return redirect('/data')
    return redirect('/login')

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        # Check if already logged in
        token = session.get('token')
        if token and get_username_from_token(token):
            return redirect('/data')
        return render_template('login.html')
    
    # POST - Handle login
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        return render_template('login.html', error='Invalid input'), 400
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        result, columns = authenticate_user(username, password_hash)
        if result:
            token = create_token(username, expiration_time=3600)  # 1 hour
            session['token'] = token
            return redirect('/data')
        else:
            return render_template('login.html', error='Invalid credentials'), 401
    except Exception as e:
        return render_template('login.html', error=str(e)), 500


@app.route('/data')
def route_data():
    token = session.get('token')
    if not token:
        return redirect('/login')
    
    username = get_username_from_token(token)
    if not username:
        return redirect('/login')
    
    try:
        result, columns = get_user_data(username)
        if result:
            data = dict(zip(columns, result))
            user_data = {
                'username': username,
                'created_at': format_datetime(data.get('created_at', '')),
                'updated_at': format_datetime(data.get('updated_at', '')),
                'card_id': data.get('card_id', ''),
                'credit': data.get('credit', 0)
            }
            return render_template('data-view.html', user=user_data)
        else:
            return render_template('data-view.html', error='No data found'), 404
    except Exception as e:
        return render_template('data-view.html', error=f'Database error: {str(e)}'), 500


@app.route('/logout')
def route_logout():
    session.pop('token', None)
    return redirect('/login')


# ==================== HTMX ENDPOINTS (Return HTML Fragments) ====================

@app.route('/update-credit', methods=['POST'])
def update_credit():
    """HTMX endpoint - updates credit and returns updated display"""
    token = session.get('token')
    if not token:
        return '<div class="alert alert-danger">Unauthorized</div>', 401
    
    username = get_username_from_token(token)
    if not username:
        return '<div class="alert alert-danger">Unauthorized</div>', 401
    
    credit = request.form.get('credit-input')
    if not credit:
        return '<div class="alert alert-danger">Invalid credit value</div>', 400
    
    try:
        update_data = {
            'credit': int(credit),
            'updated_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        }
        update_user_data(username, update_data)
        return '<div class="alert alert-success">Credit updated successfully</div>', 200
    except Exception as e:
        return f'<div class="alert alert-danger">Error: {str(e)}</div>', 500


@app.route('/change-password', methods=['POST'])
def change_password_handler():
    """HTMX endpoint - changes password and returns status message"""
    token = session.get('token')    
    
    if not token:
        return '<div class="alert alert-danger">Unauthorized</div>', 401
    
    username = get_username_from_token(token)
    if not username:
        return '<div class="alert alert-danger">Unauthorized</div>', 401
    
    current_password = request.form.get('current-password')
    new_password = request.form.get('new-password')
    confirm_password = request.form.get('confirm-password')
    
    if not current_password or not new_password or not confirm_password:
        return '<div class="alert alert-danger">All fields are required</div>', 400
    
    if new_password != confirm_password or len(new_password) < 5:
        return '<div class="alert alert-danger">New passwords do not match or is too short (at least 5 characters)</div>', 400
    
    try:
        old_hash = hashlib.sha256(current_password.encode()).hexdigest()
        new_hash = hashlib.sha256(new_password.encode()).hexdigest()
        change_password(username, old_hash, new_hash)
        return '<div class="alert alert-success">Password changed successfully</div>', 200
    except Exception as e:
        return f'<div class="alert alert-danger">Error: {str(e)}</div>', 500


if __name__ == '__main__':
    app.run(debug=True)
