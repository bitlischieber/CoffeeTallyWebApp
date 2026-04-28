import os
from azure.cosmos import CosmosClient


class DatabaseHandler_Cosmos:
    """CosmosDB database handler for CoffeeTally application."""

    def __init__(self, config):
        """Initialize CosmosDB database handler.
        
        Args:
            config: Database configuration dictionary with cosmos settings
        """
        self.cosmos_config = config.get('cosmos', {})

        # Environment variables take precedence over config file
        for key in ['endpoint', 'key', 'database_name', 'container_name']:
            env_var = f"COFFEETALLY_{key.upper()}"
            env_value = os.environ.get(env_var)
            if env_value:
                self.cosmos_config[key] = env_value

        # Initialize CosmosDB client
        self.client = CosmosClient(
            self.cosmos_config['endpoint'],
            self.cosmos_config['key']
        )
        self.database = self.client.get_database_client(self.cosmos_config['database_name'])
        self.container = self.database.get_container_client(self.cosmos_config['container_name'])

    def get_user_data(self, username):
        """Get user data by username.
        
        Args:
            username: The username to look up
            
        Returns:
            Tuple of (result, columns) where result is the user row and columns is list of column names.
            Returns (None, []) if user not found or error occurs.
        """
        try:
            query = "SELECT * FROM c WHERE c.username = @username"
            parameters = [{"name": "@username", "value": username}]

            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))

            if items:
                item = items[0]
                # Return data in format compatible with MySQL handler (tuple, columns)
                columns = ['username', 'password_hash', 'card_id', 'credit', 'created_at', 'updated_at']
                result = (
                    item.get('username'),
                    item.get('password_hash'),
                    item.get('card_id'),
                    item.get('credit'),
                    item.get('created_at'),
                    item.get('updated_at')
                )
                return result, columns
            return None, []
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
            query = "SELECT * FROM c WHERE c.username = @username AND c.password_hash = @password_hash"
            parameters = [
                {"name": "@username", "value": username},
                {"name": "@password_hash", "value": password_hash}
            ]

            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))

            if items:
                item = items[0]
                # Return data in format compatible with MySQL handler (tuple, columns)
                columns = ['username', 'password_hash', 'card_id', 'credit', 'created_at', 'updated_at']
                result = (
                    item.get('username'),
                    item.get('password_hash'),
                    item.get('card_id'),
                    item.get('credit'),
                    item.get('created_at'),
                    item.get('updated_at')
                )
                return result, columns
            return None, []
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
            # First, get the existing document
            query = "SELECT * FROM c WHERE c.username = @username"
            parameters = [{"name": "@username", "value": username}]

            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))

            if not items:
                raise Exception(f"User {username} not found")

            # Update the document
            item = items[0]
            for key, value in update_data.items():
                item[key] = value

            self.container.upsert_item(item)
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
            # Verify old password matches
            query = "SELECT * FROM c WHERE c.username = @username AND c.password_hash = @old_password_hash"
            parameters = [
                {"name": "@username", "value": username},
                {"name": "@old_password_hash", "value": old_password_hash}
            ]

            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))

            if not items:
                raise Exception("Old password does not match")

            # Update password
            item = items[0]
            item['password_hash'] = new_password_hash
            self.container.upsert_item(item)
            return True
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")

    def get_user_by_card_id(self, card_id):
        """Get user data by card_id.
        
        Args:
            card_id: The card_id to look up
            
        Returns:
            Tuple of (result, columns) where result is the user row and columns is list of column names.
            Returns (None, []) if user not found or error occurs.
        """
        try:
            query = "SELECT * FROM c WHERE c.card_id = @card_id"
            parameters = [
                {"name": "@card_id", "value": card_id},
            ]
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))

            if items:
                item = items[0]
                # Return data in format compatible with MySQL handler (tuple, columns)
                columns = ['username', 'password_hash', 'card_id', 'credit', 'created_at', 'updated_at']
                result = (
                    item.get('username'),
                    item.get('password_hash'),
                    item.get('card_id'),
                    item.get('credit'),
                    item.get('created_at'),
                    item.get('updated_at')
                )
                return result, columns
            return None, []
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")


    def authenticate_card(self, card_id):
        """Authenticate user by card_id and password hash.
        
        Args:
            card_id: The card_id to authenticate
            
        Returns:
            Tuple of (result, columns) where result is the user row if authenticated.
            Returns (None, []) if authentication fails or error occurs.
        """
        try:
            query = "SELECT * FROM c WHERE c.card_id = @card_id AND (NOT IS_DEFINED(c.password_hash) OR c.password_hash = "" OR IS_NULL(c.password_hash))"
            parameters = [
                {"name": "@card_id", "value": card_id},
            ]
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))

            if items:
                item = items[0]
                # Return data in format compatible with MySQL handler (tuple, columns)
                columns = ['username', 'password_hash', 'card_id', 'credit', 'created_at', 'updated_at']
                result = (
                    item.get('username'),
                    item.get('password_hash'),
                    item.get('card_id'),
                    item.get('credit'),
                    item.get('created_at'),
                    item.get('updated_at')                    
                )
                return result, columns
            return None, []

        except Exception as e:
            raise Exception(f"Database error: {str(e)}")

    def setup_user(self, card_id, username, name, password_hash):
        """Setup a new user with card_id by setting username and password.
        
        Args:
            card_id: The card_id to set up
            username: The username to set
            name: The name of the user
            password_hash: The hashed password to set
            
        Returns:
            True if setup was successful
            
        Raises:
            Exception if database error occurs
        """
        try:

            query = "SELECT * FROM c WHERE c.card_id = @card_id"
            parameters = [
                {"name": "@username", "value": username},
                {"name": "@name", "value": name},
                {"name": "@password_hash", "value": password_hash},
                {"name": "@card_id", "value": card_id}
            ]

            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))

            if not items:
                raise Exception("Card not found")

            # Update password
            item = items[0]
            item['username'] = username
            item['name'] = name
            item['password_hash'] = password_hash            
            self.container.upsert_item(item)
            return True
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")
