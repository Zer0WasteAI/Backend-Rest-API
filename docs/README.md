# ZeroWasteAI API Documentation 📚

Documentación completa de la API ZeroWasteAI desarrollada con Clean Architecture, Firebase Authentication y Google Gemini AI.

## 📖 Documentos Disponibles

### 🔍 [API_COMPLETE_DOCUMENTATION.md](./API_COMPLETE_DOCUMENTATION.md)
**Documentación completa de todos los módulos, endpoints y flujos**

- ✅ Arquitectura general con Clean Architecture
- ✅ Módulos y casos de uso detallados
- ✅ Controladores y endpoints con parámetros
- ✅ Modelos de dominio y relaciones
- ✅ Infraestructura y servicios externos
- ✅ Flujos principales paso a paso
- ✅ Patrones de diseño implementados

### 🔄 [DETAILED_FLOWS.md](./DETAILED_FLOWS.md)
**Flujos detallados con archivos involucrados**

- 🔐 Flujo de Autenticación (OAuth + JWT)
- 🔍 Flujo de Reconocimiento de Alimentos (IA)
- 📦 Flujo de Gestión de Inventario
- 🍳 Flujo de Generación de Recetas (IA + Async)
- 📅 Flujo de Planificación de Comidas
- 🌱 Flujo de Cálculo de Impacto Ambiental
- 🖼️ Flujo de Gestión de Imágenes

### 🏗️ [ARCHITECTURE_OVERVIEW.md](./ARCHITECTURE_OVERVIEW.md)
**Arquitectura, patrones de diseño y consideraciones técnicas**

- 🏛️ Clean Architecture implementation
- 🎯 Patrones de diseño (Factory, Repository, Strategy)
- 📁 Estructura de directorios explicada
- 🔧 Capas de la aplicación
- 🚀 Tecnologías y servicios utilizados
- 🛡️ Seguridad y autenticación
- 📈 Performance y escalabilidad

---

## 🌟 Características Principales de la API

### 🔥 Tecnologías Core
- **Framework**: Flask + Flask-JWT-Extended
- **Arquitectura**: Clean Architecture
- **Base de Datos**: MySQL + SQLAlchemy ORM
- **Autenticación**: Firebase Auth + JWT
- **IA**: Google Gemini API
- **Storage**: Firebase Storage
- **Cache**: Redis + Smart Caching

### 🎯 Funcionalidades Principales

#### 🔐 Autenticación y Usuarios
- Login con Firebase OAuth (Google, Apple, Facebook)
- JWT tokens con refresh y blacklisting
- Gestión de perfiles de usuario
- Seguridad empresarial

#### 🔍 Reconocimiento Inteligente
- Reconocimiento de alimentos por imagen
- Análisis de ingredientes con IA
- Procesamiento en lote
- Extracción de datos nutricionales

#### 📦 Gestión de Inventario
- Inventario inteligente de alimentos
- Tracking de fechas de vencimiento
- Alertas de productos próximos a vencer
- Gestión de cantidades y ubicaciones

#### 🍳 Generación de Recetas
- Generación automática basada en inventario
- Recetas personalizadas con IA
- Generación de imágenes asíncrona
- Sistema de favoritos y guardado

#### 📅 Planificación de Comidas
- Planes de comida semanales/mensuales
- Integración con inventario
- Reserva automática de ingredientes
- Calendario de comidas

#### 🌱 Impacto Ambiental
- Cálculo de ahorro de CO2
- Métricas de conservación de agua
- Reducción de desperdicio alimentario
- Reportes de sostenibilidad

#### 🖼️ Gestión de Imágenes
- Subida de imágenes a Firebase Storage
- Reconocimiento y categorización automática
- Sistema de referencias visuales
- Búsqueda de imágenes similares

---

## 🏗️ Arquitectura en Resumen

### Clean Architecture Layers:

```
🌐 Interface Layer    → Controllers, Serializers, Middlewares
🎯 Application Layer  → Use Cases, Factories, Services  
🏛️ Domain Layer       → Models, Repositories, Value Objects
🔧 Infrastructure     → Database, Firebase, AI, Security
```

### Flujo de Datos:
```
Client → Security → Rate Limit → Auth → Controller → Use Case → Repository → Database
    ←              ←            ←      ←          ←         ←          ←
```

---

## 📊 Módulos Principales

| Módulo | Use Cases | Controlador | Descripción |
|--------|-----------|-------------|-------------|
| 🔐 **Auth** | 4 | `auth_controller.py` | Autenticación OAuth + JWT |
| 👤 **User** | 2 | `user_controller.py` | Gestión de perfiles |
| 🔍 **Recognition** | 4 | `recognition_controller.py` | IA de reconocimiento |
| 📦 **Inventory** | 19 | `inventory_controller.py` | Gestión de inventario |
| 🍳 **Recipes** | 15 | `recipe_controller.py` | Generación y gestión |
| 📅 **Planning** | 6 | `planning_controller.py` | Planificación de comidas |
| 🖼️ **Images** | 5 | `image_management_controller.py` | Gestión de imágenes |
| 🌱 **Environmental** | 4 | `environmental_savings_controller.py` | Impacto ambiental |
| 🎨 **Generation** | 2 | `generation_controller.py` | Generación asíncrona |
| 🛡️ **Admin** | 2 | `admin_controller.py` | Administración |

---

## 🚀 Performance y Optimización

### 📈 Características de Performance:
- **Connection Pooling**: Pool optimizado de 20-60 conexiones MySQL
- **Smart Caching**: Cache inteligente para operaciones de IA costosas
- **Rate Limiting**: Protección por endpoint con límites personalizados
- **Async Processing**: Generación de imágenes en background
- **HTTP Compression**: Compresión gzip automática
- **Lazy Loading**: Carga bajo demanda de relaciones

### 🛡️ Características de Seguridad:
- **Firebase Authentication**: Autenticación robusta
- **JWT with Blacklisting**: Tokens seguros con invalidación
- **Security Headers**: Headers HTTP de seguridad
- **Input Validation**: Validación exhaustiva de entradas
- **SQL Injection Prevention**: ORM con prepared statements
- **CORS Configuration**: Configuración segura para web apps

---

## 📱 Endpoints Principales

### Base URL: `/api`

| Grupo | Base Path | Endpoints | Descripción |
|-------|-----------|-----------|-------------|
| 🔐 Auth | `/auth` | 3 | Login, refresh, logout |
| 👤 User | `/user` | 2 | Perfil GET/PUT |
| 🔍 Recognition | `/recognition` | 3 | Reconocimiento IA |
| 📦 Inventory | `/inventory` | 12 | CRUD inventario completo |
| 🍳 Recipes | `/recipes` | 8 | Generación y gestión |
| 📅 Planning | `/planning` | 6 | Planes de comida |
| 🖼️ Images | `/image_management` | 4 | Gestión de imágenes |
| 🌱 Environmental | `/environmental_savings` | 4 | Impacto ambiental |
| 🎨 Generation | `/generation` | 2 | Estado de generación |
| 🛡️ Admin | `/admin` | 2 | Administración interna |

---

## 📋 Casos de Uso Implementados

### Total: **67 Use Cases** distribuidos en 8 módulos

- **Autenticación**: 4 use cases (OAuth, refresh, logout)
- **Reconocimiento**: 4 use cases (foods, ingredients, batch)
- **Inventario**: 19 use cases (CRUD completo + lógica de negocio)
- **Recetas**: 15 use cases (generación IA + favoritos + ambientales)
- **Planificación**: 6 use cases (meal plans completos)
- **Imágenes**: 5 use cases (gestión + búsqueda + upload)
- **Ambiental**: 4 use cases (cálculos de impacto)
- **Otros**: 10 use cases (admin, async, utilities)

---

## 🔄 Flujos de Integración

### 🔥 Firebase Integration:
- **Authentication**: Validación de tokens Firebase
- **Storage**: Almacenamiento de imágenes
- **Firestore**: Perfiles de usuario (sync con MySQL)

### 🤖 AI Integration:
- **Gemini Pro**: Análisis de texto y generación de recetas
- **Gemini Pro Vision**: Análisis de imágenes de alimentos
- **Custom Pipeline**: Generación de imágenes de recetas

### 🗄️ Database Integration:
- **MySQL Primary**: Datos principales y transaccionales
- **Redis Cache**: Cache de operaciones costosas
- **Connection Pool**: Gestión optimizada de conexiones

---

## 📈 Métricas y Monitoreo

### 🎯 KPIs Monitoreados:
- **Response Times**: Por endpoint y operación
- **AI Usage**: Tokens consumidos y costos
- **Cache Performance**: Hit rate y efficiency
- **Database Load**: Conexiones activas y query performance
- **Error Rates**: Por tipo y endpoint
- **Security Events**: Intentos de acceso y anomalías

### 📊 Dashboards Disponibles:
- **Performance**: Tiempos de respuesta y throughput
- **Security**: Eventos de seguridad y tokens
- **AI Usage**: Consumo y costos de APIs de IA
- **Business**: Métricas de uso y engagement

---

## 🎯 Próximos Pasos y Roadmap

### 🚀 Mejoras Planificadas:
1. **Microservices Migration**: Separación por dominio
2. **GraphQL API**: Complemento a REST
3. **Real-time Features**: WebSockets para notificaciones
4. **Advanced AI**: Modelos personalizados
5. **Mobile SDKs**: SDKs nativos para iOS/Android
6. **Analytics Dashboard**: Dashboard completo de métricas

### 🔧 Optimizaciones Técnicas:
1. **Database Sharding**: Escalabilidad horizontal
2. **CDN Integration**: Distribución global de imágenes
3. **Advanced Caching**: Multi-layer caching strategy
4. **Message Queues**: RabbitMQ/Apache Kafka
5. **Container Orchestration**: Kubernetes deployment
6. **CI/CD Pipeline**: Automated testing y deployment

---

## 🤝 Contribución y Desarrollo

### 📋 Guías de Desarrollo:
1. **Seguir Clean Architecture**: Respetar separación de capas
2. **Testing Strategy**: Unit tests por use case
3. **Documentation**: Documentar nuevos endpoints
4. **Performance**: Considerar cache y rate limiting
5. **Security**: Validar inputs y manejar errores

### 🔧 Setup de Desarrollo:
```bash
# 1. Clonar repositorio
git clone <repository-url>

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env

# 4. Ejecutar migraciones
python -m src.main

# 5. Iniciar servidor de desarrollo
python -m src.main
```

---

## 📞 Contacto y Soporte

### 🌱 ZeroWasteAI Team
- **Misión**: Reducir el desperdicio alimentario a través de tecnología IA
- **Visión**: Un futuro más sustentable con tecnología inteligente
- **Valores**: Innovación, sostenibilidad, impacto social

### 🛠️ Soporte Técnico:
- **API Status**: `/status` endpoint
- **Documentation**: `/apidocs` (Swagger UI)
- **Logs**: Centralized logging system
- **Monitoring**: Real-time metrics dashboard

---

*Documentación generada para ZeroWasteAI API v1.0.0*  
*Clean Architecture + Firebase + JWT + AI Integration*  
*Desarrollado con ❤️ para un futuro más sustentable* 🌍🌱