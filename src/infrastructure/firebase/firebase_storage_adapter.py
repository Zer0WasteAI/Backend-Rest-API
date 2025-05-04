from firebase_admin import credentials, initialize_app, storage
from io import BytesIO
import firebase_admin
from src.config.config import Config
from pathlib import Path

if not firebase_admin._apps:
    cred_path = Path(Config.FIREBASE_CREDENTIALS_PATH).resolve()
    if not cred_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de credenciales en {cred_path.resolve()}")
    cred = credentials.Certificate(str(cred_path))
    initialize_app(cred, {
        "storageBucket": Config.FIREBASE_STORAGE_BUCKET
    })

def get_image_from_firebase(path_in_bucket: str) -> BytesIO:
    try:
        bucket = storage.bucket()
        blob = bucket.blob(path_in_bucket)
        if not blob.exists():
            raise FileNotFoundError(f"La imagen '{path_in_bucket}' no existe en el bucket.")
        image_bytes = blob.download_as_bytes()
        return BytesIO(image_bytes)
    except Exception as e:
        raise RuntimeError(f"Error al obtener la imagen '{path_in_bucket}': {e}")
