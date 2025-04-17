from flask import Flask
from config.db_config import init_db


app = Flask(__name__)
init_db(app)

@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'

if __name__ == '__main__':
    app.run(debug=True)