import time
import secrets
from flask import request

# Simple token storage (in production, use a database or Redis)
tokens = {}


def validate_token():
    """Validate token from Authorization header and return username if valid."""
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
    """Get username from token if token is valid."""
    if token not in tokens:
        return None
    if time.time() > tokens[token]['expires']:
        del tokens[token]
        return None
    return tokens[token]['username']


def create_token(username, expiration_time=3600):
    """Create a new token for the given username.
    
    Args:
        username: The username to create token for
        expiration_time: Token expiration time in seconds (default: 1 hour)
    
    Returns:
        The generated token string
    """
    token = secrets.token_hex(32)
    tokens[token] = {'username': username, 'expires': time.time() + expiration_time}
    return token


def invalidate_token(token):
    """Remove a token from storage."""
    if token in tokens:
        del tokens[token]
