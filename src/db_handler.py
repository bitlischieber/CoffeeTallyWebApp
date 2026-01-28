import pymysql
import json
import os

# Load database config
with open('config.json', 'r') as f:
    config = json.load(f)

db_config = config.get('database', {})
for key in ['host', 'port', 'user', 'password', 'database', 'table']:
    env_var = f"COFFEETALLY_{key.upper()}"
    if key not in db_config or not db_config[key]:
        db_config[key] = os.environ.get(env_var)


def get_db_connection():
    """Create and return a database connection."""
    return pymysql.connect(
        host=db_config['host'],
        port=int(db_config['port']),
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database']
    )


def get_user_data(username):
    """Get user data by username.
    
    Args:
        username: The username to look up
        
    Returns:
        Tuple of (result, columns) where result is the user row and columns is list of column names.
        Returns (None, []) if user not found or error occurs.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = f"SELECT * FROM {db_config['table']} WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        cursor.close()
        conn.close()
        return result, columns
    except Exception as e:
        raise Exception(f"Database error: {str(e)}")


def authenticate_user(username, password_hash):
    """Authenticate user by username and password hash.
    
    Args:
        username: The username to authenticate
        password_hash: The hashed password to verify
        
    Returns:
        Tuple of (result, columns) where result is the user row if authenticated.
        Returns (None, []) if authentication fails or error occurs.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = f"SELECT * FROM {db_config['table']} WHERE username = %s AND password_hash = %s"
        cursor.execute(query, (username, password_hash))
        result = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        cursor.close()
        conn.close()
        return result, columns
    except Exception as e:
        raise Exception(f"Database error: {str(e)}")


def update_user_data(username, update_data):
    """Update user data in database.
    
    Args:
        username: The username to update
        update_data: Dictionary of column names to values to update
        
    Returns:
        True if update was successful
        
    Raises:
        Exception if database error occurs
    """
    try:
        set_clause = ', '.join(f"{k} = %s" for k in update_data.keys())
        values = list(update_data.values()) + [username]
        query = f"UPDATE {db_config['table']} SET {set_clause} WHERE username = %s"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        raise Exception(f"Database error: {str(e)}")


def change_password(username, old_password_hash, new_password_hash):
    """Change user password if old password matches.
    
    Args:
        username: The username to change password for
        old_password_hash: The hashed old password to verify
        new_password_hash: The hashed new password to set
        
    Returns:
        True if password was changed successfully
        
    Raises:
        Exception if old password doesn't match or database error occurs
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify old password matches
        query = f"SELECT password_hash FROM {db_config['table']} WHERE username = %s AND password_hash = %s"
        cursor.execute(query, (username, old_password_hash))
        result = cursor.fetchone()
        
        if not result:
            raise Exception("Old password does not match")
        
        # Update password
        query = f"UPDATE {db_config['table']} SET password_hash = %s WHERE username = %s"
        cursor.execute(query, (new_password_hash, username))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        raise Exception(f"Database error: {str(e)}")
