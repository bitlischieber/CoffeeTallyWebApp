from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def hello():
    return render_template_string('''
    <head>
    <title>Flask Hello World</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    </head>
    <body class="bg-light p-5">
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-8 text-center">
                    <h1 class="display-4 text-primary mb-4">Hello World from Flask!</h1>
                    <button class="btn btn-outline-success btn-lg px-4" 
                            hx-get="/data" 
                            hx-target="#result"
                            hx-swap="innerHTML">
                        Load Data
                    </button>
                    <div id="result" class="mt-5 p-4 bg-white rounded shadow">
                        Click to see MySQL data here
                    </div>
                </div>
            </div>
        </div>
    </body>
    ''')

@app.route('/data')
def data():
    # TODO: Replace with MySQL query
    return '<p>Data from MySQL: Hello 42!</p>'

if __name__ == '__main__':
    app.run(debug=True)
