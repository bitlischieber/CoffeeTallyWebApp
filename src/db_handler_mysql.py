import pymysql
import os


class DatabaseHandler_MySQL:
    """MySQL database handler for CoffeeTally application."""
    
    def __init__(self, config):
        """Initialize MySQL database handler.
        
        Args:
            config: Database configuration dictionary with mysql settings
        """
        self.db_config = config.get('mysql', {})
        
        # Environment variables take precedence over config file
        for key in ['host', 'port', 'user', 'password', 'database', 'table']:
            env_var = f"COFFEETALLY_{key.upper()}"
            env_value = os.environ.get(env_var)
            if env_value:
                self.db_config[key] = env_value
    
    def get_db_connection(self):
        """Create and return a database connection."""
        return pymysql.connect(
            host=self.db_config['host'],
            port=int(self.db_config['port']),
            user=self.db_config['user'],
            password=self.db_config['password'],
            database=self.db_config['database']
        )
    
    def get_user_data(self, username):
        """Get user data by username.
        
        Args:
            username: The username to look up
            
        Returns:
            Tuple of (result, columns) where result is the user row and columns is list of column names.
            Returns (None, []) if user not found or error occurs.
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            query = f"SELECT * FROM {self.db_config['table']} WHERE username = %s"
            cursor.execute(query, (username,))
            result = cursor.fetchone()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            cursor.close()
            conn.close()
            return result, columns
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")
    
    def authenticate_user(self, username, password_hash):
        """Authenticate user by username and password hash.
        
        Args:
            username: The username to authenticate
            password_hash: The hashed password to verify
            
        Returns:
            Tuple of (result, columns) where result is the user row if authenticated.
            Returns (None, []) if authentication fails or error occurs.
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            query = f"SELECT * FROM {self.db_config['table']} WHERE username = %s AND password_hash = %s"
            cursor.execute(query, (username, password_hash))
            result = cursor.fetchone()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            cursor.close()
            conn.close()
            return result, columns
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")
    
    def update_user_data(self, username, update_data):
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
            query = f"UPDATE {self.db_config['table']} SET {set_clause} WHERE username = %s"
            
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute(query, values)
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")
    
    def change_password(self, username, old_password_hash, new_password_hash):
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
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Verify old password matches
            query = f"SELECT password_hash FROM {self.db_config['table']} WHERE username = %s AND password_hash = %s"
            cursor.execute(query, (username, old_password_hash))
            result = cursor.fetchone()
            
            if not result:
                raise Exception("Old password does not match")
            
            # Update password
            query = f"UPDATE {self.db_config['table']} SET password_hash = %s WHERE username = %s"
            cursor.execute(query, (new_password_hash, username))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")
