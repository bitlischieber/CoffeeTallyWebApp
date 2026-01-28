from flask import Flask, render_template_string, request, jsonify, redirect, session
import hashlib
from datetime import datetime, timezone
from token_handler import validate_token, get_username_from_token, create_token
from db_handler import get_user_data, authenticate_user, update_user_data, change_password

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change to a secure key in production

# HTML constants
HTML_HEAD = '''<head>
<title>Coffee Tally</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="https://unpkg.com/htmx.org@1.9.10"></script>
</head>'''


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


def build_user_display_html(result, columns):
    """Build HTML for user data display with editable credit and password change."""
    # Map columns to values
    data = dict(zip(columns, result))
    
    created_at = data.get('created_at', '')
    updated_at = data.get('updated_at', '')
    card_id = data.get('card_id', '')
    credit = data.get('credit', 0)
    
    created_at_formatted = format_datetime(created_at)
    updated_at_formatted = format_datetime(updated_at)
    
    return f'''
    <!DOCTYPE html>
    <html>
    {HTML_HEAD}
    <body class="bg-light p-5">
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card shadow">
                    <div class="card-body">
                        <h2 class="card-title text-center mb-4">Your Account</h2>
                        
                        <!-- User Info Section -->
                        <div class="mb-4">
                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <label class="form-label fw-bold">Register date</label>
                                    <p class="form-control-plaintext">{created_at_formatted}</p>
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label fw-bold">Last credit change</label>
                                    <p class="form-control-plaintext">{updated_at_formatted}</p>
                                </div>
                            </div>
                            
                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <label class="form-label fw-bold">Card id</label>
                                    <p class="form-control-plaintext">{card_id}</p>
                                </div>
                            </div>
                            
                            <!-- Credit Section -->
                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <label for="credit-input" class="form-label fw-bold">Credit</label>
                                    <div class="input-group">
                                        <input type="number" class="form-control" id="credit-input" value="{credit}" step="1">
                                        <button class="btn btn-primary" type="button" hx-post="/update-credit" hx-include="#credit-input" hx-trigger="click">Update</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <hr>
                        
                        <!-- Change Password Section -->
                        <div class="mb-4">
                            <h5 class="mb-3">Change password</h5>
                            <div class="mb-3">
                                <label for="current-password" class="form-label">Current password</label>
                                <input type="password" class="form-control" id="current-password" placeholder="Enter current password">
                            </div>
                            <div class="mb-3">
                                <label for="new-password" class="form-label">New password</label>
                                <input type="password" class="form-control" id="new-password" placeholder="Enter new password">
                            </div>
                            <div class="mb-3">
                                <label for="confirm-password" class="form-label">Confirm new password</label>
                                <input type="password" class="form-control" id="confirm-password" placeholder="Confirm new password">
                            </div>
                            <button class="btn btn-warning" type="button" hx-post="/change-password" hx-include="#current-password,#new-password,#confirm-password" hx-trigger="click">Change password</button>
                            <div id="password-message" class="mt-2"></div>
                        </div>
                        
                        <button class="btn btn-secondary mt-3 float-end" onclick="window.location.href='/logout'">Logout</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    </body>
    </html>
    '''

@app.route('/')
def route_index():
    token = session.get('token')
    if token:
        username = get_username_from_token(token)
        if username:
            return redirect('/data')
    
    # Show login form
    return render_template_string(f'''
    {HTML_HEAD}
    <body class="bg-light p-5">
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card shadow">
                        <div class="card-body">
                            <h2 class="card-title text-center mb-4">Login to Coffee Tally</h2>
                            <form hx-post="/login" hx-target="#result" hx-swap="innerHTML">
                                <div class="mb-3">
                                    <label for="username" class="form-label">Username</label>
                                    <input type="text" class="form-control" id="username" name="username" required>
                                    <label for="password" class="form-label">Password</label>
                                    <input type="password" class="form-control" id="password" name="password" required>
                                </div>
                                <button type="submit" class="btn btn-primary w-100">Login</button>
                            </form>
                            <div id="result" class="mt-3"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    ''')

@app.route('/logout')
def route_logout():
    session.pop('token', None)
    return redirect('/')


@app.route('/update-credit', methods=['POST'])
def update_credit():
    token = session.get('token')
    if not token:
        return '<p class="text-danger">Unauthorized</p>', 401
    
    username = get_username_from_token(token)
    if not username:
        return '<p class="text-danger">Unauthorized</p>', 401
    
    credit = request.form.get('credit-input')
    if not credit:
        return '<p class="text-danger">Invalid credit value</p>', 400
    
    try:
        update_data = {
            'credit': int(credit),
            'updated_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        }
        update_user_data(username, update_data)
        return '<p class="text-success">Credit updated successfully</p>'
    except Exception as e:
        return f'<p class="text-danger">Error: {str(e)}</p>', 500


@app.route('/change-password', methods=['POST'])
def change_pwd():
    token = session.get('token')
    if not token:
        return '<p class="text-danger">Unauthorized</p>', 401
    
    username = get_username_from_token(token)
    if not username:
        return '<p class="text-danger">Unauthorized</p>', 401
    
    current_password = request.form.get('current-password')
    new_password = request.form.get('new-password')
    confirm_password = request.form.get('confirm-password')
    
    if not current_password or not new_password or not confirm_password:
        return '<p class="text-danger">All fields are required</p>', 400
    
    if new_password != confirm_password:
        return '<p class="text-danger">New passwords do not match</p>', 400
    
    try:
        old_hash = hashlib.sha256(current_password.encode()).hexdigest()
        new_hash = hashlib.sha256(new_password.encode()).hexdigest()
        change_password(username, old_hash, new_hash)
        return '<p class="text-success">Password changed successfully</p>'
    except Exception as e:
        return f'<p class="text-danger">Error: {str(e)}</p>', 500

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return jsonify({'error': 'Invalid input'}), 400
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        result, columns = authenticate_user(username, password_hash)
        if result:
            token = create_token(username, expiration_time=3600)  # 1 hour
            session['token'] = token
            return redirect('/data')
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/data', methods=['GET', 'POST', 'PUT'])
def route_data():
    if request.method == 'GET':
        token = session.get('token')
        if not token:
            return 'Unauthorized', 401
        username = get_username_from_token(token)
        if not username:
            return 'Unauthorized', 401
        
        try:
            result, columns = get_user_data(username)
            if result:
                return build_user_display_html(result, columns)
            else:
                return 'No data found', 404
        except Exception as e:
            return f'Database error: {str(e)}', 500
    
    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            return '<p class="text-danger">Invalid input</p>'
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            result, columns = authenticate_user(username, password_hash)
            if result:
                return build_user_display_html(result, columns)
            else:
                return '<p class="text-danger">Invalid credentials</p>'
        except Exception as e:
            return f'<p class="text-danger">Database error: {str(e)}</p>'
    
    elif request.method == 'PUT':
        username = validate_token()
        if not username:
            return jsonify({'error': 'Unauthorized'}), 401
        
        update_data = request.json
        if not update_data:
            return jsonify({'error': 'No data provided'}), 400
        
        try:
            update_user_data(username, update_data)
            return jsonify({'message': 'Updated successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
