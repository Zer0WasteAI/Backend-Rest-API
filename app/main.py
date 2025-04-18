from flask import Flask, Blueprint
from config.db_config import init_db
from interface.controllers.recognition_controller import recognition_bp

app = Flask(__name__)
init_db(app)

# global blueprint for api
api_bp = Blueprint('api', __name__, url_prefix='/api')

# other blueprints
api_bp.register_blueprint(recognition_bp, url_prefix='/recognition')

# root blueprint
app.register_blueprint(api_bp)

@app.route('/')
def all_works():  # put application's code here
    return 'API is working!'

if __name__ == '__main__':
    app.run(debug=True)