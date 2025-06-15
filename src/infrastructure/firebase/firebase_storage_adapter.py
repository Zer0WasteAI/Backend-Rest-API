from firebase_admin import credentials, initialize_app, storage
from io import BytesIO
import firebase_admin
from pathlib import Path
from src.config.config import Config
import re

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

    def get_image(self, path_or_url: str) -> BytesIO:
        """
        Obtiene una imagen desde Firebase Storage.
        Puede recibir una URL completa de Firebase Storage o una ruta del bucket.
        """
        # Si es una URL completa de Firebase Storage, extraer la ruta del bucket
        if path_or_url.startswith('https://storage.googleapis.com/'):
            bucket_path = self._extract_bucket_path_from_url(path_or_url)
        else:
            bucket_path = path_or_url
        
        print(f"🔍 Buscando imagen en bucket path: {bucket_path}")
        
        blob = self.bucket.blob(bucket_path)
        if not blob.exists():
            # Si no existe, intentar buscar en la estructura legacy
            legacy_path = self._try_legacy_path(bucket_path)
            if legacy_path:
                print(f"🔍 Intentando con ruta legacy: {legacy_path}")
                blob = self.bucket.blob(legacy_path)
                if not blob.exists():
                    raise FileNotFoundError(f"La imagen '{bucket_path}' no existe en el bucket (tampoco en legacy: '{legacy_path}').")
            else:
                raise FileNotFoundError(f"La imagen '{bucket_path}' no existe en el bucket.")
        
        print(f"✅ Imagen encontrada en: {blob.name}")
        return BytesIO(blob.download_as_bytes())
    
    def _extract_bucket_path_from_url(self, url: str) -> str:
        """
        Extrae la ruta del bucket desde una URL completa de Firebase Storage.
        Ejemplo: 
        https://storage.googleapis.com/zer0wasteai-91408.firebasestorage.app/uploads/ingredient/ad36bbebfa4a412598cb79bd190e6515.jpg
        -> uploads/ingredient/ad36bbebfa4a412598cb79bd190e6515.jpg
        """
        # Patrón para extraer la ruta después del bucket name
        pattern = r'https://storage\.googleapis\.com/[^/]+/(.+)'
        match = re.match(pattern, url)
        if match:
            return match.group(1)
        else:
            # Fallback: tomar todo después de la última barra
            return url.split('/')[-1]
    
    def _try_legacy_path(self, current_path: str) -> str:
        """
        Intenta generar una ruta legacy si la ruta actual no funciona.
        Por ejemplo, si tenemos uploads/ingredient/file.jpg, intentar con uploads/UID/ingredient/file.jpg
        """
        # Si la ruta ya tiene estructura de UID, no hay legacy que probar
        if current_path.startswith('uploads/') and current_path.count('/') >= 3:
            return None
        
        # Si es una ruta simple como uploads/ingredient/file.jpg, 
        # no podemos adivinar el UID, así que retornamos None
        return None

    def list_blobs(self, prefix: str = "", valid_extensions=None, recursive=True):
        blobs = self.bucket.list_blobs(prefix=prefix)

        if not recursive:
            prefix_depth = prefix.strip("/").count("/")
            blobs = [b for b in blobs if b.name.strip("/").count("/") == prefix_depth]

        if valid_extensions:
            blobs = [blob for blob in blobs if any(blob.name.lower().endswith(ext) for ext in valid_extensions)]

        return blobs
