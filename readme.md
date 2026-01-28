# CoffeeTally Webapp

---
Work in progress. Currently the app is not in stable working state!
---

This is the web application for self-managing data for the [CoffeeTally](https://github.com/bitlischieber/CoffeeTally) project.

## Setup

### Prerequisites
- python3
- flask

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

## Running the App

Start the development server:
```bash
cd src
.\venv\Scripts\activate.bat
flask run
```

The app will usually be available at `http://127.0.0.1:5000`.