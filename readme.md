# CoffeeTally Webapp

---
Work in progress. Currently the app is not in stable working state!
---

This is the web application for self-managing data for the [CoffeeTally](https://github.com/bitlischieber/CoffeeTally) project.

## Features

- Support for multiple database providers:
  - **MySQL**: Traditional relational database
  - **Azure Cosmos DB**: NoSQL cloud database service
- Configurable database provider via `config.json`
- User authentication and session management
- Credit management for coffee purchases
- Password change functionality

## Setup

### Prerequisites
- python3
- flask
- One of the following databases:
  - MySQL server (for MySQL provider)
  - Azure Cosmos DB account (for Cosmos provider)

### Development Environment

1. Clone the repository
2. Install environment and dependencies:
    ```bash
    cd src
    python -m venv venv
    .\venv\Scripts\activate.bat
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

3. Configure the database connection:
    - Copy `config.json.template` to `config.json`
    - Update the database connection parameters in `config.json`
    
### Database Configuration

The application supports two database providers: **MySQL** and **Azure Cosmos DB**.

#### MySQL Configuration

Set `database_provider` to `"mysql"` in `config.json`:

```json
{
  "database_provider": "mysql",
  "database": {
    "mysql": {
      "host": "localhost",
      "port": 3306,
      "user": "your_mysql_user",
      "password": "your_mysql_password",
      "database": "coffee_tally",
      "table": "coffee_tally_users"
    }
  }
}
```

#### Azure Cosmos DB Configuration

Set `database_provider` to `"cosmos"` in `config.json`:

```json
{
  "database_provider": "cosmos",
  "database": {
    "cosmos": {
      "endpoint": "https://your-account.documents.azure.com:443/",
      "key": "your-cosmos-db-primary-key",
      "database_name": "coffee_tally",
      "container_name": "users"
    }
  }
}
```

**Note:** Cosmos DB documents should have the following fields (same as MySQL):
- `username` (string, partition key recommended)
- `password_hash` (string)
- `card_id` (string)
- `credit` (number)
- `created_at` (string, ISO 8601 format)
- `updated_at` (string, ISO 8601 format)

#### Environment Variables

Database configuration can be overridden using environment variables. **Environment variables always take precedence over `config.json` settings when set**, making them ideal for production deployments where credentials should not be stored in configuration files.

**Configuration Priority:**
1. Environment variables (highest priority - always used when set)
2. `config.json` settings (fallback when environment variables are not set)

**Database Provider:**
- `COFFEETALLY_DATABASE_PROVIDER` - Set to `"mysql"` or `"cosmos"` to override provider selection

**For MySQL:**
- `COFFEETALLY_HOST` - MySQL server hostname
- `COFFEETALLY_PORT` - MySQL server port
- `COFFEETALLY_USER` - MySQL username
- `COFFEETALLY_PASSWORD` - MySQL password
- `COFFEETALLY_DATABASE` - MySQL database name
- `COFFEETALLY_TABLE` - MySQL table name

**For Cosmos DB:**
- `COFFEETALLY_ENDPOINT` - Cosmos DB endpoint URL
- `COFFEETALLY_KEY` - Cosmos DB primary or secondary key
- `COFFEETALLY_DATABASE_NAME` - Cosmos DB database name
- `COFFEETALLY_CONTAINER_NAME` - Cosmos DB container name

**Example: Production deployment with environment variables**
```bash
# Set database provider
export COFFEETALLY_DATABASE_PROVIDER=mysql

# Set MySQL credentials (overrides any values in config.json)
export COFFEETALLY_HOST=production-db-server.com
export COFFEETALLY_PORT=3306
export COFFEETALLY_USER=coffeetally_user
export COFFEETALLY_PASSWORD=secure_password_here
export COFFEETALLY_DATABASE=coffee_tally
export COFFEETALLY_TABLE=coffee_tally_users
```

**Example: Mixed configuration (partial override)**
```bash
# Use host and credentials from environment, other values from config.json
export COFFEETALLY_HOST=production-db-server.com
export COFFEETALLY_PASSWORD=secure_password_here
# Port, user, database, and table will be read from config.json
```

## Running the App

Start the development server:
```bash
cd src
.\venv\Scripts\activate.bat
flask run
```

The app will usually be available at `http://127.0.0.1:5000`.