import firebase_admin
from firebase_admin import firestore
from pathlib import Path
from src.config.config import Config
import logging

logger = logging.getLogger(__name__)

class FirestoreProfileService:
    def __init__(self):
        # Inicializar Firestore client
        if not firebase_admin._apps:
            cred_path = Path(Config.FIREBASE_CREDENTIALS_PATH).resolve()
            if not cred_path.exists():
                raise FileNotFoundError(f"No se encontró el archivo de credenciales en {cred_path}")
            
            cred = firebase_admin.credentials.Certificate(str(cred_path))
            firebase_admin.initialize_app(cred)
        
        self.db = firestore.client()
        self.users_collection = self.db.collection('users')

    def get_profile(self, uid: str) -> dict:
        """
        Obtiene el perfil completo del usuario desde Firestore
        """
        try:
            doc_ref = self.users_collection.document(uid)
            doc = doc_ref.get()
            
            if doc.exists:
                profile_data = doc.to_dict()
                logger.info(f"Profile loaded from Firestore for UID: {uid}")
                return self._format_profile_response(profile_data, uid)
            else:
                logger.warning(f"Profile not found in Firestore for UID: {uid}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting profile from Firestore for UID {uid}: {str(e)}")
            raise

    def update_profile(self, uid: str, update_data: dict) -> dict:
        """
        Actualiza el perfil del usuario en Firestore
        """
        try:
            doc_ref = self.users_collection.document(uid)
            
            # Preparar datos para actualización
            firestore_data = self._prepare_firestore_data(update_data)
            
            # Actualizar en Firestore
            doc_ref.update(firestore_data)
            logger.info(f"Profile updated in Firestore for UID: {uid}")
            
            # Retornar perfil actualizado
            return self.get_profile(uid)
            
        except Exception as e:
            logger.error(f"Error updating profile in Firestore for UID {uid}: {str(e)}")
            raise

    def create_profile(self, uid: str, profile_data: dict) -> dict:
        """
        Crea un nuevo perfil en Firestore
        """
        try:
            doc_ref = self.users_collection.document(uid)
            
            # Preparar datos iniciales
            firestore_data = self._prepare_initial_profile_data(profile_data, uid)
            
            # Crear en Firestore
            doc_ref.set(firestore_data)
            logger.info(f"Profile created in Firestore for UID: {uid}")
            
            # Obtener el perfil recién creado (esto resuelve los SERVER_TIMESTAMP)
            return self.get_profile(uid)
            
        except Exception as e:
            logger.error(f"Error creating profile in Firestore for UID {uid}: {str(e)}")
            raise

    def _format_profile_response(self, firestore_data: dict, uid: str) -> dict:
        """
        Formatea la respuesta del perfil para el API
        """
        def format_timestamp(timestamp):
            """Convierte timestamp de Firestore a string ISO"""
            if timestamp is None:
                return None
            # Si es un timestamp de Firestore, convertir a string
            if hasattr(timestamp, 'isoformat'):
                return timestamp.isoformat()
            elif hasattr(timestamp, 'timestamp'):
                from datetime import datetime
                return datetime.fromtimestamp(timestamp.timestamp()).isoformat()
            else:
                return str(timestamp)
        
        return {
            "uid": uid,
            "displayName": firestore_data.get("displayName", ""),
            "email": firestore_data.get("email", ""),
            "photoURL": firestore_data.get("photoURL"),
            "emailVerified": firestore_data.get("emailVerified", False),
            "authProvider": firestore_data.get("authProvider", "unknown"),
            "language": firestore_data.get("language", "es"),
            "cookingLevel": firestore_data.get("cookingLevel", "beginner"),
            "measurementUnit": firestore_data.get("measurementUnit", "metric"),
            "allergies": firestore_data.get("allergies", []),
            "allergyItems": firestore_data.get("allergyItems", []),
            "preferredFoodTypes": firestore_data.get("preferredFoodTypes", []),
            "specialDietItems": firestore_data.get("specialDietItems", []),
            "favoriteRecipes": firestore_data.get("favoriteRecipes", []),
            "initialPreferencesCompleted": firestore_data.get("initialPreferencesCompleted", False),
            "createdAt": format_timestamp(firestore_data.get("createdAt")),
            "lastLoginAt": format_timestamp(firestore_data.get("lastLoginAt"))
        }

    def _prepare_firestore_data(self, update_data: dict) -> dict:
        """
        Prepara los datos para actualización en Firestore
        """
        firestore_data = {}
        
        # Mapeo de campos del API a Firestore
        field_mapping = {
            "name": "displayName",
            "displayName": "displayName",
            "email": "email",
            "photo_url": "photoURL",
            "photoURL": "photoURL",
            "language": "language",
            "cookingLevel": "cookingLevel",
            "measurementUnit": "measurementUnit",
            "allergies": "allergies",
            "allergyItems": "allergyItems",
            "preferredFoodTypes": "preferredFoodTypes",
            "specialDietItems": "specialDietItems",
            "favoriteRecipes": "favoriteRecipes",
            "initialPreferencesCompleted": "initialPreferencesCompleted"
        }
        
        for api_field, firestore_field in field_mapping.items():
            if api_field in update_data:
                firestore_data[firestore_field] = update_data[api_field]
        
        # Manejar campo prefs especial (para compatibilidad)
        if "prefs" in update_data and isinstance(update_data["prefs"], dict):
            for key, value in update_data["prefs"].items():
                if key in field_mapping:
                    firestore_data[field_mapping[key]] = value
                else:
                    firestore_data[key] = value
        
        return firestore_data

    def _prepare_initial_profile_data(self, profile_data: dict, uid: str) -> dict:
        """
        Prepara datos iniciales para un nuevo perfil
        """
        import firebase_admin.firestore
        
        initial_data = {
            "id": uid,
            "displayName": profile_data.get("name", profile_data.get("displayName", "")),
            "email": profile_data.get("email", ""),
            "photoURL": profile_data.get("photo_url", profile_data.get("photoURL")),
            "emailVerified": profile_data.get("email_verified", False),
            "authProvider": profile_data.get("auth_provider", "unknown"),
            "language": "es",
            "cookingLevel": "beginner",
            "measurementUnit": "metric",
            "allergies": [],
            "allergyItems": [],
            "preferredFoodTypes": [],
            "specialDietItems": [],
            "favoriteRecipes": [],
            "initialPreferencesCompleted": False,
            "createdAt": firebase_admin.firestore.SERVER_TIMESTAMP,
            "lastLoginAt": firebase_admin.firestore.SERVER_TIMESTAMP
        }
        
        return initial_data

    def sync_with_mysql(self, uid: str, mysql_profile_repo):
        """
        Sincroniza datos de Firestore con MySQL para caché
        """
        try:
            firestore_profile = self.get_profile(uid)
            if firestore_profile:
                # Preparar datos para MySQL
                mysql_data = {
                    "name": firestore_profile.get("displayName", ""),
                    "phone": "",  # MySQL specific field
                    "photo_url": firestore_profile.get("photoURL", ""),
                    "prefs": {
                        "language": firestore_profile.get("language"),
                        "cookingLevel": firestore_profile.get("cookingLevel"),
                        "measurementUnit": firestore_profile.get("measurementUnit"),
                        "allergies": firestore_profile.get("allergies"),
                        "preferredFoodTypes": firestore_profile.get("preferredFoodTypes"),
                        "specialDietItems": firestore_profile.get("specialDietItems")
                    }
                }
                
                # Actualizar o crear en MySQL
                existing_profile = mysql_profile_repo.find_by_uid(uid)
                if existing_profile:
                    mysql_profile_repo.update(uid, mysql_data)
                else:
                    mysql_data["uid"] = uid
                    mysql_profile_repo.create(mysql_data)
                
                logger.info(f"Profile synced with MySQL for UID: {uid}")
                
        except Exception as e:
            logger.error(f"Error syncing profile with MySQL for UID {uid}: {str(e)}") 