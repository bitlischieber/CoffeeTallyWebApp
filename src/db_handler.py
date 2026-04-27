"""
Database handler middleware - Provides a unified interface for different database providers.
Supports MySQL and CosmosDB backends based on configuration.
"""

import json
import os
from db_handler_mysql import DatabaseHandler_MySQL
from db_handler_cosmos import DatabaseHandler_Cosmos


# Load database config
with open('config.json', 'r') as f:
    config = json.load(f)

# Get database provider from environment variable or config
# Environment variable takes precedence
database_provider = os.environ.get('COFFEETALLY_DATABASE_PROVIDER')
if not database_provider:
    database_provider = config.get('database_provider', 'mysql')

database_config = config.get('database', {})

# Initialize the appropriate database handler based on provider
if database_provider == 'cosmos':
    _db_handler = DatabaseHandler_Cosmos(database_config)
elif database_provider == 'mysql':
    _db_handler = DatabaseHandler_MySQL(database_config)
else:
    raise ValueError(f"Unsupported database provider: {database_provider}")


# Expose the database handler methods as module-level functions
# This maintains backward compatibility with existing code

def get_user_data(username):
    """Get user data by username.
    
    Args:
        username: The username to look up
        
    Returns:
        Tuple of (result, columns) where result is the user row and columns is list of column names.
        Returns (None, []) if user not found or error occurs.
    """
    return _db_handler.get_user_data(username)


def authenticate_user(username, password_hash):
    """Authenticate user by username and password hash.
    
    Args:
        username: The username to authenticate
        password_hash: The hashed password to verify
        
    Returns:
        Tuple of (result, columns) where result is the user row if authenticated.
        Returns (None, []) if authentication fails or error occurs.
    """
    return _db_handler.authenticate_user(username, password_hash)


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
    return _db_handler.update_user_data(username, update_data)


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
    return _db_handler.change_password(username, old_password_hash, new_password_hash)
