# CoffeeTally Webapp

This is the web application for self-managing data for the [CoffeeTally](https://github.com/bitlischieber/CoffeeTally) project.

## Setup

### Prerequisites
- python3
- flask

### Development Environment

1. Clone the repository
2. Install environment and dependencies:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate.bat
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

3. Configure the database connection:
    - Copy `config.json.template` to `config.json`
    - Update the database connection parameters in `config.json`

4. Set the Flask secret key (required outside development):
    - Set `FLASK_SECRET_KEY` to a long random value
    - Optional for local dev: set `FLASK_ENV=development` to use the dev fallback

## Running the App

Start the development server:
```bash
cd src
.\venv\Scripts\activate.bat
set FLASK_ENV=development
set FLASK_SECRET_KEY=dev-only-change-me
flask run
```

The app will usually be available at `http://127.0.0.1:5000`.
