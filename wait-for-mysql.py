import time
import pymysql
import os

host = os.getenv("MYSQL_HOST", "mysql_db")
port = int(os.getenv("MYSQL_PORT", 3306))
user = os.getenv("MYSQL_USER", "user")
password = os.getenv("MYSQL_PASSWORD", "userpass")
database = os.getenv("MYSQL_DATABASE", "zwaidb")

while True:
    try:
        print(f"🔄 Intentando conectar a MySQL en {host}:{port}...")
        conn = pymysql.connect(host=host, port=port, user=user, password=password, database=database)
        print("✅ ¡MySQL está listo!")
        conn.close()
        break
    except Exception as e:
        print("❌ Esperando MySQL:", e)
        time.sleep(3)
