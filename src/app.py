from flask import Flask, render_template_string, request, jsonify, redirect, session
import json
import os
import pymysql
import hashlib
import secrets
import time

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change to a secure key in production

# Load database config
with open('config.json', 'r') as f:
    config = json.load(f)

db_config = config.get('database', {})
for key in ['host', 'port', 'user', 'password', 'database', 'table']:
    env_var = f"COFFEETALLY_{key.upper()}"
    if key not in db_config or not db_config[key]:
        db_config[key] = os.environ.get(env_var)

# Now db_config contains the database connection settings

# Simple token storage (in production, use a database or Redis)
tokens = {}

def validate_token():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    token = auth_header[7:]
    if token not in tokens:
        return None
    if time.time() > tokens[token]['expires']:
        del tokens[token]
        return None
    return tokens[token]['username']

def get_username_from_token(token):
    if token not in tokens:
        return None
    if time.time() > tokens[token]['expires']:
        del tokens[token]
        return None
    return tokens[token]['username']

@app.route('/')
def hello():
    token = session.get('token')
    if token:
        username = get_username_from_token(token)
        if username:
            # Show data page
            try:
                conn = pymysql.connect(
                    host=db_config['host'],
                    port=int(db_config['port']),
                    user=db_config['user'],
                    password=db_config['password'],
                    database=db_config['database']
                )
                cursor = conn.cursor()
                query = f"SELECT * FROM {db_config['table']} WHERE username = %s"
                cursor.execute(query, (username,))
                result = cursor.fetchone()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                cursor.close()
                conn.close()
                
                if result:
                    # Generate HTML table with the data
                    table_html = '<table class="table table-striped"><thead><tr>'
                    for col in columns:
                        table_html += f'<th>{col}</th>'
                    table_html += '</tr></thead><tbody><tr>'
                    for value in result:
                        table_html += f'<td>{value}</td>'
                    table_html += '</tr></tbody></table>'
                    return f'''
                    <!DOCTYPE html>
                    <html>
                    <head>
                    <title>Your Data</title>
                    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
                    </head>
                    <body class="bg-light p-5">
                    <div class="container">
                        <h2 class="text-center mb-4">Your Data</h2>
                        {table_html}
                        <button class="btn btn-secondary mt-3" onclick="window.location.href='/logout'">Logout</button>
                    </div>
                    </body>
                    </html>
                    '''
                else:
                    # No data, show login
                    pass
            except Exception as e:
                # Error, show login
                pass
    
    # Show login form
    return render_template_string('''
    <head>
    <title>Coffee Tally Login</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    </head>
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
def logout():
    session.pop('token', None)
    return redirect('/')
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return jsonify({'error': 'Invalid input'}), 400
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        conn = pymysql.connect(
            host=db_config['host'],
            port=int(db_config['port']),
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database']
        )
        cursor = conn.cursor()
        query = f"SELECT * FROM {db_config['table']} WHERE username = %s AND password_hash = %s"
        cursor.execute(query, (username, password_hash))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            token = secrets.token_hex(32)
            tokens[token] = {'username': username, 'expires': time.time() + 3600}  # 1 hour
            session['token'] = token
            return redirect('/data')
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/data', methods=['GET', 'POST', 'PUT'])
def data():
    if request.method == 'GET':
        token = session.get('token')
        if not token:
            return 'Unauthorized', 401
        username = get_username_from_token(token)
        if not username:
            return 'Unauthorized', 401
        
        try:
            conn = pymysql.connect(
                host=db_config['host'],
                port=int(db_config['port']),
                user=db_config['user'],
                password=db_config['password'],
                database=db_config['database']
            )
            cursor = conn.cursor()
            query = f"SELECT * FROM {db_config['table']} WHERE username = %s"
            cursor.execute(query, (username,))
            result = cursor.fetchone()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            cursor.close()
            conn.close()
            
            if result:
                # Generate HTML table with the data
                table_html = '<table class="table table-striped"><thead><tr>'
                for col in columns:
                    table_html += f'<th>{col}</th>'
                table_html += '</tr></thead><tbody><tr>'
                for value in result:
                    table_html += f'<td>{value}</td>'
                table_html += '</tr></tbody></table>'
                return f'''
                <!DOCTYPE html>
                <html>
                <head>
                <title>Your Data</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
                </head>
                <body class="bg-light p-5">
                <div class="container">
                    <h2 class="text-center mb-4">Your Data</h2>
                    {table_html}
                    <button class="btn btn-secondary mt-3" onclick="window.location.href='/logout'">Logout</button>
                </div>
                </body>
                </html>
                '''
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
            conn = pymysql.connect(
                host=db_config['host'],
                port=int(db_config['port']),
                user=db_config['user'],
                password=db_config['password'],
                database=db_config['database']
            )
            cursor = conn.cursor()
            query = f"SELECT * FROM {db_config['table']} WHERE username = %s AND password_hash = %s"
            cursor.execute(query, (username, password_hash))
            result = cursor.fetchone()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            cursor.close()
            conn.close()
            
            if result:
                # Generate HTML table with the data
                table_html = '<table class="table table-striped"><thead><tr>'
                for col in columns:
                    table_html += f'<th>{col}</th>'
                table_html += '</tr></thead><tbody><tr>'
                for value in result:
                    table_html += f'<td>{value}</td>'
                table_html += '</tr></tbody></table>'
                return f'''
                <div class="container">
                    <h2 class="text-center mb-4">Your Data</h2>
                    {table_html}
                    <button class="btn btn-secondary mt-3" onclick="window.location.reload()">Logout</button>
                </div>
                '''
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
        
        set_clause = ', '.join(f"{k} = %s" for k in update_data.keys())
        values = list(update_data.values()) + [username]
        query = f"UPDATE {db_config['table']} SET {set_clause} WHERE username = %s"
        
        try:
            conn = pymysql.connect(
                host=db_config['host'],
                port=int(db_config['port']),
                user=db_config['user'],
                password=db_config['password'],
                database=db_config['database']
            )
            cursor = conn.cursor()
            cursor.execute(query, values)
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'message': 'Updated successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
