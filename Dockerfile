# Imagen base oficial
FROM python:3.11-slim

# Crear carpeta de trabajo
WORKDIR /app

# Copiar dependencias
COPY requirements.txt .

# Instalar dependencias
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiar todo el código de la app
COPY . .

# Asegura que Python no guarde bytecode (.pyc)
ENV PYTHONUNBUFFERED=1

# Exponer puerto
EXPOSE 3000

# El comando real se define en docker-compose (con wait-for-mysql)
# Imagen base oficial
FROM python:3.11-slim

# Crear carpeta de trabajo
WORKDIR /app

# Copiar dependencias
COPY requirements.txt .

# Instalar dependencias
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiar todo el código de la app
COPY . .

# Asegura que Python no guarde bytecode (.pyc)
ENV PYTHONUNBUFFERED=1

# Exponer puerto
EXPOSE 3000

# El comando real se define en docker-compose (con wait-for-mysql)
# Imagen base oficial
FROM python:3.11-slim

# Crear carpeta de trabajo
WORKDIR /app

# Copiar dependencias
COPY requirements.txt .

# Instalar dependencias
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiar todo el código de la app
COPY . .

# Asegura que Python no guarde bytecode (.pyc)
ENV PYTHONUNBUFFERED=1

# Exponer puerto
EXPOSE 3000

# El comando real se define en docker-compose (con wait-for-mysql)
CMD ["sh", "-c", "python wait-for-mysql.py && python src/main.py"]