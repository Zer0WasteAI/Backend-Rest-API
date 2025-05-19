from firebase_admin import credentials, initialize_app, storage
from io import BytesIO
import firebase_admin
from pathlib import Path
from src.config.config import Config

if not firebase_admin._apps:
    cred_path = Path(Config.FIREBASE_CREDENTIALS_PATH).resolve()
    if not cred_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de credenciales en {cred_path.resolve()}")
    cred = credentials.Certificate(str(cred_path))
    initialize_app(cred, {
        "storageBucket": Config.FIREBASE_STORAGE_BUCKET
    })

class FirebaseStorageAdapter:
    def __init__(self):
        self.bucket = storage.bucket()

    def get_image(self, path_in_bucket: str) -> BytesIO:
        blob = self.bucket.blob(path_in_bucket)
        if not blob.exists():
            raise FileNotFoundError(f"La imagen '{path_in_bucket}' no existe en el bucket.")
        return BytesIO(blob.download_as_bytes())

    def list_blobs(self, prefix: str = "", valid_extensions=None, recursive=True):
        blobs = self.bucket.list_blobs(prefix=prefix)

        if not recursive:
            prefix_depth = prefix.strip("/").count("/")
            blobs = [b for b in blobs if b.name.strip("/").count("/") == prefix_depth]

        if valid_extensions:
            blobs = [blob for blob in blobs if any(blob.name.lower().endswith(ext) for ext in valid_extensions)]

        return blobs
