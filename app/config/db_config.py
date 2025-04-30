from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv # Uses the .env
import os

db = SQLAlchemy()

def init_db(app):
    load_dotenv()  # Load environment variables from .env file

    print("DB URI:", os.getenv("DB_USER"), os.getenv("DB_PASSWORD"))

    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)