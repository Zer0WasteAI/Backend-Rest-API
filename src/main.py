import time
from sqlalchemy.exc import OperationalError
from sqlalchemy.sql import text
from flasgger import Swagger
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from src.config.config import Config
from src.infrastructure.db.schemas.user_schema import db
from src.config.swagger_config import swagger_config, swagger_template

from src.interface.controllers.auth_controller import auth_bp
from src.interface.controllers.admin_controller import admin_bp
from src.interface.controllers.image_management_controller import image_management_bp
from src.interface.controllers.planning_controller import planning_bp
from src.interface.controllers.user_controller import user_bp
from src.interface.controllers.recognition_controller import recognition_bp
from src.interface.controllers.inventory_controller import inventory_bp
from src.interface.controllers.recipe_controller import recipes_bp
from src.interface.controllers.generation_controller import generation_bp
from src.interface.controllers.environmental_savings_controller import environmental_savings_bp

from src.shared.exceptions.base import AppException
from src.infrastructure.auth.jwt_callbacks import configure_jwt_callbacks
from src.infrastructure.security.security_headers import add_security_headers

# Importar modelos ORM para que se creen las tablas
from src.infrastructure.db.models.recipe_orm import RecipeORM
from src.infrastructure.db.models.inventory_orm import InventoryORM
from src.infrastructure.db.models.ingredient_orm import IngredientORM
from src.infrastructure.db.models.ingredient_stack_orm import IngredientStackORM
from src.infrastructure.db.models.food_item_orm import FoodItemORM
from src.infrastructure.db.models.image_reference_orm import ImageReferenceORM
from src.infrastructure.db.models.recognition_orm import RecognitionORM
from src.infrastructure.db.models.async_task_orm import AsyncTaskORM
from src.infrastructure.db.models.daily_meal_plan_orm import DailyMealPlanORM
from src.infrastructure.db.models.generation_orm import GenerationORM
from src.infrastructure.db.models.environmental_savings_orm import EnvironmentalSavingsORM

def create_app():
    application = Flask(__name__)
    CORS(application)
    application.config.from_object(Config)
    
    # Configurar headers de seguridad
    add_security_headers(application)
    
    Swagger(application, config=swagger_config, template=swagger_template)
    db.init_app(application)
    
    # Configurar JWT con callbacks de seguridad
    jwt_manager = JWTManager(application)
    configure_jwt_callbacks(jwt_manager)

    # Registrar blueprints de API
    application.register_blueprint(auth_bp, url_prefix='/api/auth')
    application.register_blueprint(user_bp, url_prefix='/api/user')
    application.register_blueprint(recognition_bp, url_prefix='/api/recognition')
    application.register_blueprint(image_management_bp, url_prefix='/api/image_management')
    application.register_blueprint(admin_bp, url_prefix='/api/admin')
    application.register_blueprint(inventory_bp, url_prefix='/api/inventory')
    application.register_blueprint(recipes_bp, url_prefix='/api/recipes')
    application.register_blueprint(planning_bp, url_prefix='/api/planning')
    application.register_blueprint(generation_bp, url_prefix='/api/generation')
    application.register_blueprint(environmental_savings_bp, url_prefix='/api/environmental_savings')

    @application.errorhandler(AppException)
    def handle_app_exception(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @application.route('/')
    def welcome():
        return jsonify({
            "message": "¡Bienvenido a ZeroWasteAI API! 🌱",
            "description": "API para reconocimiento de alimentos y gestión de inventario inteligente",
            "version": "1.0.0",
            "architecture": "Clean Architecture with Firebase Authentication + JWT",
            "features": [
                "🔥 Autenticación con Firebase + JWT",
                "👤 Gestión de perfiles de usuario",
                "🤖 Reconocimiento de alimentos con IA",
                "📦 Gestión inteligente de inventario",
                "🍳 Generación de recetas con IA",
                "📸 Gestión de imágenes de referencia",
                "🛡️ Seguridad empresarial con headers y token blacklisting"
            ],
            "endpoints": {
                "authentication": "/api/auth",
                "user_profile": "/api/user",
                "food_recognition": "/api/recognition",
                "inventory_management": "/api/inventory",
                "recipe_generation": "/api/recipes",
                "image_management": "/api/image_management",
                "admin_panel": "/api/admin",
                "api_status": "/status",
                "documentation": "/apidocs"
            },
            "security_features": [
                "Firebase Authentication integration",
                "JWT with token blacklisting",
                "Security headers middleware",
                "Refresh token tracking",
                "Admin role-based access"
            ],
            "team": "ZeroWasteAI Development Team",
            "mission": "Reducir el desperdicio alimentario a través de tecnología IA",
            "contact": "Desarrollado con ❤️ para un futuro más sustentable 🌍"
        }), 200

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
                from src.infrastructure.db.schemas.token_blacklist_schema import TokenBlacklist, RefreshTokenTracking

                for model, name in [
                    (User, "users"), 
                    (AuthUser, "auth_users"), 
                    (ProfileUser, "profile_users"),
                    (TokenBlacklist, "token_blacklist"),
                    (RefreshTokenTracking, "refresh_token_tracking")
                ]:
                    try:
                        count = db.session.query(model).count()
                        table_status[name] = {"exists": True, "records": count}
                    except Exception as err:
                        table_status[name] = {"exists": False, "error": str(err)}

                return jsonify({
                    "status": "success",
                    "message": "✅ Conexión exitosa a la base de datos",
                    "architecture": "Firebase Auth + JWT + Clean Architecture",
                    "database_name": database_name,
                    "database_info": db_info,
                    "known_tables": tables,
                    "table_status": table_status,
                    "security_status": {
                        "jwt_security": "Active",
                        "token_blacklisting": "Enabled",
                        "security_headers": "Configured",
                        "firebase_integration": "Active"
                    }
                }), 200

        except OperationalError as err:
            return jsonify({
                "status": "error",
                "message": f"❌ Error de conexión a la base de datos: {str(err)}",
                "tables": [],
                "database_name": None,
                "database_info": {}
            }), 500
        except Exception as ex:
            return jsonify({
                "status": "error",
                "message": f"❌ Error inesperado: {str(ex)}"
            }), 500

    return application

print(f"📦 URI: {Config.SQLALCHEMY_DATABASE_URI}")
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
        print("🔥 Firebase Authentication + JWT Security: Activado")
        print("🛡️ Security Headers: Configurados")
        print("🌱 ZeroWasteAI API: Lista para reducir desperdicio alimentario!")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)