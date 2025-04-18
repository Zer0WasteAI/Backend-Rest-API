import time
from sqlalchemy.exc import OperationalError
from sqlalchemy.sql import text
from flasgger import Swagger
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from src.config.config import Config
from src.infrastructure.db.schemas.user_schema import db
from src.interface.controllers.auth_controller import auth_bp
from src.config.swagger_config import swagger_config, swagger_template
from src.interface.controllers.user_controller import user_bp


def create_app():
    application = Flask(__name__)
    CORS(application)
    application.config.from_object(Config)
    Swagger(application, config=swagger_config, template=swagger_template)
    db.init_app(application)
    JWTManager(application)

    application.register_blueprint(auth_bp, url_prefix='/api/auth')
    application.register_blueprint(user_bp, url_prefix='/api/user')

    @application.route('/')
    def welcome():
        return "Welcome to the ZeroWasteAI API!"

    @application.route('/status', methods=['GET'])
    def status():
        try:
            with application.app_context():
                db.session.execute(text('SELECT 1'))
                tables = list(db.metadata.tables.keys())
                database_name = db.engine.url.database
                db_info = {
                    "host": Config.DB_HOST,
                    "port": Config.DB_PORT,
                    "name": Config.DB_NAME,
                    "user": Config.DB_USER
                }

                table_status = {}
                from src.infrastructure.db.schemas.user_schema import User
                from src.infrastructure.db.schemas.auth_user_schema import AuthUser
                from src.infrastructure.db.schemas.profile_user_schema import ProfileUser

                for model, name in [(User, "users"), (AuthUser, "auth_users"), (ProfileUser, "profile_users")]:
                    try:
                        count = db.session.query(model).count()
                        table_status[name] = {"exists": True, "records": count}
                    except Exception as err:
                        table_status[name] = {"exists": False, "error": str(err)}

                return jsonify({
                    "status": "success",
                    "message": "Conexión exitosa a la base de datos",
                    "database_name": database_name,
                    "database_info": db_info,
                    "known_tables": tables,
                    "table_status": table_status
                }), 200

        except OperationalError as err:
            return jsonify({
                "status": "error",
                "message": f"Error de conexión a la base de datos: {str(err)}",
                "tables": [],
                "database_name": None,
                "database_info": {}
            }), 500
        except Exception as ex:
            return jsonify({
                "status": "error",
                "message": f"Error inesperado: {str(ex)}"
            }), 500

    return application


app = create_app()

with app.app_context():
    success = False
    for attempt in range(10):
        try:
            print(f"🔁 Intentando conectar a la base de datos... intento {attempt + 1}")
            db.create_all()
            print("✅ Tablas creadas:")
            print(db.metadata.tables.keys())
            success = True
            break
        except OperationalError as e:
            print(f"❌ Fallo en la conexión a la base de datos: {e}")
            time.sleep(3)

    if not success:
        print("🚨 No se pudo conectar a la base de datos después de varios intentos")
        exit(1)
    else:
        print("🎉 Inicialización exitosa: La base de datos está lista.")


