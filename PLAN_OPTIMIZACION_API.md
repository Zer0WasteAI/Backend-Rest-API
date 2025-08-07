# Plan de Optimización API - 50-100 Peticiones Concurrentes

## 📊 Análisis Actual de la Arquitectura

### ✅ **Fortalezas Identificadas**
- **Caching inteligente**: Redis + Flask-Caching implementado con estrategias específicas por endpoint
- **Rate limiting**: Sistema configurado por tipos de endpoint (AI, CRUD, Auth)
- **Clean Architecture**: Separación clara de responsabilidades
- **Optimización AI**: Cache específico para operaciones costosas de IA (3600s para impacto ambiental)

### ⚠️ **Cuellos de Botella Identificados**

#### 1. **Base de Datos - CRÍTICO**
- **MySQL single instance** sin pooling optimizado
- **Conexiones síncronas** sin async/await
- **Sin read replicas** para distribución de carga
- **Queries N+1** potenciales en relaciones ORM

#### 2. **Servidor de Aplicaciones - ALTO**
- **Flask development server** (no apto para producción)
- **Sin workers múltiples** 
- **Threads limitadas** por GIL de Python
- **Blocking I/O** en operaciones de base de datos

#### 3. **Concurrencia - ALTO**
- **No async/await** en endpoints críticos
- **Operaciones AI síncronas** (Gemini, reconocimiento)
- **File uploads bloqueantes**

#### 4. **Infraestructura - MEDIO**
- **Container único** sin load balancer
- **Sin auto-scaling**
- **Memoria/CPU no optimizadas**

---

## 🎯 Plan de Optimización - Orden de Prioridad

### **FASE 1: Quick Wins (1-2 días) - Mejora inmediata 2-3x**

#### 1.1 **Servidor de Producción - CRÍTICO**
```bash
# Reemplazar Flask dev server con Gunicorn + Nginx
pip install gunicorn gevent
```

**Implementación:**
- **Gunicorn** con workers gevent (async)
- **Nginx** como reverse proxy y load balancer
- **Worker processes**: 2 * CPU cores + 1
- **Configuración**: 4-6 workers para 50-100 requests

#### 1.2 **Database Connection Pooling - CRÍTICO**
```python
# Optimizar SQLAlchemy pool
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 20,           # Conexiones permanentes
    'max_overflow': 40,        # Conexiones adicionales
    'pool_timeout': 30,        # Timeout esperando conexión
    'pool_recycle': 3600,      # Reciclar conexiones cada hora
    'pool_pre_ping': True      # Validar conexiones
}
```

#### 1.3 **Redis Performance Tuning - ALTO**
```python
# Optimizar configuración Redis
REDIS_URL = 'redis://localhost:6379/0'
REDIS_CONNECTION_POOL = {
    'max_connections': 50,
    'retry_on_timeout': True,
    'socket_keepalive': True,
    'socket_keepalive_options': {}
}
```

### **FASE 2: Concurrencia (2-3 días) - Mejora 3-5x**

#### 2.1 **Async Endpoints Críticos**
Convertir a async/await:
- `/api/recognition/*` (AI operations)
- `/api/inventory/bulk` (batch operations)  
- `/api/generation/*` (recipe generation)

```python
# Ejemplo implementación
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import asyncio
import asyncpg

@inventory_bp.route("/bulk-add", methods=["POST"])
@jwt_required()
async def add_bulk_ingredients():
    # Operación async para 50-100 items simultáneos
    await process_ingredients_async(ingredients_data)
```

#### 2.2 **Background Jobs para AI**
```python
# Celery + Redis para operaciones AI pesadas
from celery import Celery

celery = Celery('zerowasteai')
celery.conf.broker_url = 'redis://localhost:6379/1'

@celery.task
def process_ai_recognition_async(image_data, user_id):
    # Procesamiento AI en background
    result = gemini_adapter.analyze_image(image_data)
    cache_service.set(f"recognition:{user_id}", result, 3600)
    return result
```

### **FASE 3: Base de Datos (3-4 días) - Mejora 2-4x**

#### 3.1 **Query Optimization**
```python
# Eager loading para evitar N+1 queries
def get_user_inventory_optimized(user_id):
    return db.session.query(Inventory)\
        .options(joinedload(Inventory.ingredients))\
        .options(joinedload(Inventory.food_items))\
        .filter_by(user_id=user_id)\
        .all()

# Índices específicos
CREATE INDEX idx_inventory_user_expiration ON inventory(user_id, expiration_date);
CREATE INDEX idx_ingredients_name_type ON ingredients(name, storage_type);
```

#### 3.2 **Database Read Replicas**
```yaml
# docker-compose.yml - Agregar replica
mysql-replica:
  image: mysql:8.0
  command: --server-id=2 --log-bin=mysql-bin --binlog-do-db=zwaidb
  environment:
    MYSQL_MASTER_SERVICE: mysql
```

### **FASE 4: Infraestructura (2-3 días) - Mejora 2-3x**

#### 4.1 **Container Orchestration**
```yaml
# docker-compose-production.yml
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - app1
      - app2

  app1: &app
    build: .
    environment:
      - WORKER_ID=1
    depends_on:
      - mysql
      - redis

  app2:
    <<: *app
    environment:
      - WORKER_ID=2

  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

#### 4.2 **Nginx Load Balancer**
```nginx
upstream backend {
    least_conn;
    server app1:3000 max_fails=3 fail_timeout=30s;
    server app2:3000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Cache estático
    location /static/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## 📈 **Métricas Esperadas de Performance**

### **Situación Actual Estimada:**
- **Concurrencia**: 5-10 requests simultáneas
- **Response time**: 200-500ms (endpoints simples), 2-5s (AI)
- **Throughput**: ~20 requests/segundo

### **Después de Optimizaciones:**

| Fase | Concurrencia | Response Time | Throughput | Mejora |
|------|-------------|---------------|------------|---------|
| **Fase 1** | 25-30 req | 100-200ms | 60 req/s | **3x** |
| **Fase 2** | 50-70 req | 80-150ms | 120 req/s | **6x** |
| **Fase 3** | 70-90 req | 50-100ms | 180 req/s | **9x** |
| **Fase 4** | 100+ req | 50-80ms | 250 req/s | **12x** |

---

## ⚡ **Quick Actions - Implementar Hoy**

### 1. **Dockerfile Optimizado**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar servidor de producción
RUN pip install gunicorn gevent

COPY . .

ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

EXPOSE 3000

# Usar Gunicorn en lugar de Flask dev server
CMD ["gunicorn", "--bind", "0.0.0.0:3000", "--workers", "4", "--worker-class", "gevent", "--worker-connections", "1000", "src.main:app"]
```

### 2. **Database Config Mejorada**
```python
# src/config/config.py - Agregar
class ProductionConfig(Config):
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'max_overflow': 40,  
        'pool_timeout': 30,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'echo': False  # Desactivar debug SQL
    }
    
    # Redis optimizado
    REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
    CACHE_REDIS_CONNECTION_POOL_KWARGS = {
        'max_connections': 50,
        'retry_on_timeout': True
    }
```

### 3. **Docker Compose Mejorado**
```yaml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    container_name: redis_cache
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
    networks:
      - auth_net

  mysql:
    image: mysql:8.0
    container_name: mysql_db
    command: --innodb-buffer-pool-size=512M --max-connections=300
    environment:
      MYSQL_DATABASE: zwaidb
      MYSQL_ROOT_PASSWORD: rootpass
      MYSQL_USER: user
      MYSQL_PASSWORD: userpass
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    networks:
      - auth_net

  backend:
    build: .
    container_name: zerowasteai_api
    depends_on:
      - mysql
      - redis
    environment:
      FLASK_ENV: production
      REDIS_URL: redis://redis:6379/0
      DB_HOST: mysql_db
    networks:
      - auth_net
```

---

## 🔧 **Monitoreo y Testing**

### **Herramientas de Load Testing:**
```bash
# Apache Bench - Testing básico
ab -n 1000 -c 50 http://localhost:3000/api/inventory/

# JMeter - Testing avanzado
# Configurar:
# - 50-100 threads (usuarios)
# - Ramp-up 30 segundos
# - Loop 10 veces
# - Assertions de response time < 500ms
```

### **Métricas a Monitorear:**
- **Response time percentiles** (P50, P95, P99)
- **Error rate** (< 1%)
- **Database connections** en uso
- **Redis hit ratio** (> 80%)
- **CPU/Memory usage** (< 70%)

---

## 💰 **Costo vs Beneficio**

| Optimización | Esfuerzo | Costo | Impacto | ROI |
|--------------|----------|-------|---------|-----|
| **Gunicorn + Workers** | 2h | $0 | +200% | ⭐⭐⭐⭐⭐ |
| **DB Pool + Redis** | 4h | $0 | +150% | ⭐⭐⭐⭐⭐ |
| **Async Endpoints** | 16h | $0 | +100% | ⭐⭐⭐⭐ |
| **Load Balancer** | 8h | $10/mes | +80% | ⭐⭐⭐⭐ |

**Inversión total**: ~30 horas desarrollo + $10/mes infraestructura  
**Resultado**: API capaz de manejar 100+ peticiones concurrentes

---

Este plan te permitirá escalar de ~10 peticiones concurrentes actuales a 100+ peticiones con una inversión mínima y mejoras incrementales probadas.