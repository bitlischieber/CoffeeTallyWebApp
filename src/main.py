from flask import Flask, render_template, request, redirect, session, make_response
import hashlib
import os
from datetime import datetime, timezone
from token_handler import get_username_from_token, create_token
from db_handler import (get_user_data, authenticate_user, update_user_data,
                         change_password, authenticate_card, setup_user)

app = Flask(__name__, template_folder='html', static_folder='html', static_url_path='/static')
secret_key = os.environ.get('FLASK_SECRET_KEY')
is_dev = os.environ.get('FLASK_ENV') == 'development' or os.environ.get('FLASK_DEBUG') == '1'
if not secret_key:
    if is_dev:
        secret_key = 'dev-only-change-me'
    else:
        raise RuntimeError('FLASK_SECRET_KEY is required in non-development environments')
app.secret_key = secret_key

def format_datetime(dt):
    """Format datetime to local timezone for display (YYYY-MM-DD HH:MM:SS)."""
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except:
            return dt
    if isinstance(dt, datetime):
        # Treat naive datetime as UTC, then convert to local timezone
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone().strftime('%Y-%m-%d %H:%M:%S')
    return str(dt)


def is_hex_string(s):
    """Check if string is a valid hex string."""
    try:
        int(s, 16)
        return True
    except (ValueError, TypeError):
        return False


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
    is_htmx = request.headers.get('HX-Request') == 'true'
    def render_login_error(message, status_code):
        if is_htmx:
            return f'<div class="alert alert-danger">{message}</div>', status_code
        return render_template('login.html', error=message), status_code

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
        return render_login_error('Invalid input', 400)

    password_hash = hashlib.sha256(password.encode()).hexdigest()

    try:
        # Check if username is a hex string (card_id)
        if is_hex_string(username) and username == password:
            result, columns = authenticate_card(username)
            if result:
                data = dict(zip(columns, result))
                # If username and password_hash are both NULL, this card needs setup
                if data.get('username') is None and data.get('password_hash') is None:
                    session['setup_card_id'] = username
                    if is_htmx:
                        response = make_response('', 204)
                        response.headers['HX-Redirect'] = '/setup'
                        return response
                    return redirect('/setup')
                else:
                    # Card has been set up, login normally with the stored username
                    actual_username = data.get('username')
                    token = create_token(actual_username, expiration_time=3600)
                    session['token'] = token
                    if is_htmx:
                        response = make_response('', 204)
                        response.headers['HX-Redirect'] = '/data'
                        return response
                    return redirect('/data')

        # Standard username/password authentication
        result, columns = authenticate_user(username, password_hash)
        if result:
            token = create_token(username, expiration_time=3600)  # 1 hour
            session['token'] = token
            if is_htmx:
                response = make_response('', 204)
                response.headers['HX-Redirect'] = '/data'
                return response
            return redirect('/data')
        else:
            return render_login_error('Invalid credentials', 401)
    except Exception as e:
        return render_login_error(str(e), 500)


@app.route('/setup', methods=['GET', 'POST'])
def setup():
    """Setup page for new users with card_id."""
    is_htmx = request.headers.get('HX-Request') == 'true'
    def render_setup_error(message, status_code):
        if is_htmx:
            return f'<div class="alert alert-danger">{message}</div>', status_code
        return render_template('setup.html', card_id=card_id, error=message), status_code

    if request.method == 'GET':
        card_id = session.get('setup_card_id')
        if not card_id:
            return redirect('/login')
        return render_template('setup.html', card_id=card_id)

    # POST - Handle setup
    card_id = session.get('setup_card_id')
    if not card_id:
        if is_htmx:
            return '<div class="alert alert-danger">No card ID in session</div>', 400
        return render_template('setup.html', error='No card ID in session'), 400

    username = request.form.get('username')
    name = request.form.get('name')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm-password')

    if not username or not name or not password or not confirm_password:
        return render_setup_error('All fields are required', 400)

    if password != confirm_password:
        return render_setup_error('Passwords do not match', 400)

    if len(username) != 7:
        return render_setup_error('Short must be exactly 7 characters', 400)

    if len(name) < 5:
        return render_setup_error('Name must be at least 5 characters', 400)

    if len(password) < 6:
        return render_setup_error('Password must be at least 6 characters', 400)

    try:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        setup_user(card_id, username, name, password_hash)

        # Clear setup session and redirect to login
        session.pop('setup_card_id', None)
        if is_htmx:
            response = make_response('', 204)
            response.headers['HX-Redirect'] = '/login'
            return response
        return redirect('/login')
    except Exception as e:
        return render_setup_error(str(e), 500)


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
