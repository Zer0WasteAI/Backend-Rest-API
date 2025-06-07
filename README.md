# 🌱 ZeroWasteAI Backend REST API

## 🎯 Overview
**ZeroWasteAI** is a sophisticated Flask-based REST API designed to combat food waste through AI-powered food recognition and intelligent inventory management. The system helps users optimize their food consumption, reduce waste, and make environmentally conscious decisions.

## 🏗️ Architecture

### **Clean Architecture Implementation**
The project follows **Clean Architecture** principles with **Domain-Driven Design (DDD)**:

```
src/
├── 📂 domain/           # Business logic & entities
├── 📂 application/      # Use cases & services  
├── 📂 infrastructure/   # External integrations
└── 📂 interface/        # API controllers & serializers
```

### **Technology Stack**

#### **🔥 Authentication & Security**
- **Firebase Authentication** - Primary authentication system
- **JWT Tokens** - API access control with token blacklisting
- **Flask-JWT-Extended** - Enhanced JWT security features
- **Security Headers** - Production-ready security middleware

#### **🤖 AI & Machine Learning**
- **Google Generative AI** - Food recognition and recipe generation
- **Google Vision API** - Advanced image processing
- **Pillow** - Image processing and manipulation

#### **🌐 Web Framework**
- **Flask 3.1.0** - Core web framework
- **Flask-CORS** - Cross-origin request support
- **Flasgger** - API documentation with Swagger

#### **🗄️ Database & Storage**
- **MySQL 8.0** - Primary database
- **SQLAlchemy 2.0** - ORM and database abstraction
- **Firebase Storage** - Image and file storage

## 🚀 Key Features

### **🔐 Authentication System**
- **Firebase Integration** - Secure, scalable user management
- **JWT Token Management** - With blacklisting for secure logout
- **Multi-platform Support** - Ready for web and mobile apps

### **🤖 AI-Powered Food Recognition**
- **Image Recognition** - Identify food items from photos
- **Nutritional Analysis** - Extract detailed nutrition information
- **Smart Categorization** - Automated food classification

### **📦 Intelligent Inventory Management**
- **Real-time Tracking** - Monitor food items and quantities
- **Expiration Alerts** - Reduce waste with smart notifications
- **Usage Analytics** - Track consumption patterns

### **🍳 AI Recipe Generation**
- **Inventory-based Recipes** - Generate meals from available ingredients
- **Nutritional Optimization** - Health-conscious meal planning
- **Waste Reduction Focus** - Maximize ingredient utilization

### **👤 User Management**
- **Profile Customization** - Dietary preferences and restrictions
- **Nutritional Goals** - Personalized health targets
- **Usage History** - Track food waste reduction progress

### **🛠️ Admin Panel**
- **System Monitoring** - Real-time API health checks
- **User Management** - Administrative user operations
- **Analytics Dashboard** - System usage statistics

## 🔌 API Endpoints

### **Authentication (`/api/auth`)**
```
POST   /login          # Firebase authentication
POST   /logout         # Secure token invalidation
POST   /refresh        # Token refresh
GET    /verify         # Token validation
```

### **User Management (`/api/user`)**
```
GET    /profile        # Get user profile
PUT    /profile        # Update profile
GET    /preferences    # Dietary preferences
PUT    /preferences    # Update preferences
```

### **Food Recognition (`/api/recognition`)**
```
POST   /analyze        # Analyze food image
GET    /history        # Recognition history
POST   /feedback       # Improve recognition
```

### **Inventory (`/api/inventory`)**
```
GET    /items          # List inventory items
POST   /items          # Add new item
PUT    /items/:id      # Update item
DELETE /items/:id      # Remove item
GET    /expiring       # Get expiring items
```

### **Recipes (`/api/recipes`)**
```
POST   /generate       # Generate recipe from inventory
GET    /saved          # Saved recipes
POST   /save           # Save recipe
GET    /:id            # Get specific recipe
```

### **Admin (`/api/admin`)**
```
GET    /stats          # System statistics
GET    /users          # User management
GET    /health         # System health check
```

## 🐳 Docker Setup

### **Quick Start**
```bash
# Clone repository
git clone https://github.com/Zer0WasteAI/Backend-Rest-API.git
cd Backend-Rest-API

# Setup environment variables
cp .env.example .env
# Configure Firebase credentials

# Start services
docker-compose up -d

# API available at http://localhost:3000
```

### **Container Architecture**
```yaml
services:
  mysql:      # Database (Port 3306)
  backend:    # Flask API (Port 3000)
```

### **Environment Variables**
```bash
# Database Configuration
DB_HOST=mysql_db
DB_NAME=zwaidb
DB_USER=user
DB_PASS=userpass

# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=src/config/firebase_credentials.json
FIREBASE_STORAGE_BUCKET=your-bucket.firebasestorage.app

# Security
JWT_SECRET_KEY=your-jwt-secret
FLASK_ENV=development
```

## 🗄️ Database Schema

### **Core Tables**
```sql
users                    # Basic user information
auth_users              # Firebase authentication data  
profile_users           # User preferences & settings
token_blacklist         # Revoked JWT tokens
refresh_token_tracking  # Session management
inventory_items         # User food inventory
food_database           # Recognized food information
recipes                 # Generated recipes
nutritional_data        # Food nutrition facts
```

## 🛡️ Security Features

### **Authentication Flow**
1. **Firebase Authentication** - User login/registration
2. **Firebase ID Token** - Server-side validation
3. **JWT Token Issuance** - Internal API access
4. **Token Blacklisting** - Secure logout
5. **Session Management** - Refresh token tracking

### **Security Headers**
- Content Security Policy (CSP)
- X-Frame-Options
- X-Content-Type-Options
- Strict-Transport-Security
- X-XSS-Protection

## 📊 Monitoring & Health

### **Health Check Endpoint**
```
GET /status
```

Returns:
- Database connection status
- Table information
- System health metrics
- Performance statistics

### **API Documentation**
- **Swagger UI**: `http://localhost:3000/apidocs`
- **Interactive testing** of all endpoints
- **Request/response examples**
- **Authentication requirements**

## 🌍 Environmental Impact

### **Food Waste Reduction**
- **Smart Inventory** - Prevent food spoilage
- **Recipe Optimization** - Use available ingredients
- **Consumption Tracking** - Monitor waste patterns
- **Educational Insights** - Promote sustainable habits

## 🔧 Development

### **Project Structure**
```
Backend-Rest-API/
├── 🐳 docker-compose.yml    # Container orchestration
├── 📋 Dockerfile           # Container configuration  
├── 📦 requirements.txt     # Python dependencies
├── ⏳ wait-for-mysql.py    # Database connection helper
├── 🧪 test/                # Test suites
└── 📂 src/                 # Application source code
   ├── 📂 application/      # Use cases & business services
   ├── 📂 config/          # Configuration files
   ├── 📂 domain/          # Core business logic
   ├── 📂 infrastructure/  # External integrations
   ├── 📂 interface/       # API controllers
   ├── 📂 shared/          # Common utilities
   └── 📄 main.py          # Application entry point
```

### **Code Quality**
- **Clean Architecture** - Separation of concerns
- **SOLID Principles** - Maintainable design
- **Type Hints** - Enhanced code clarity
- **Error Handling** - Comprehensive exception management
- **Security Best Practices** - Production-ready security

## 🚀 Deployment

### **Production Checklist**
- [ ] Firebase credentials configured
- [ ] Environment variables set
- [ ] Database migrations run
- [ ] SSL certificates installed
- [ ] Security headers enabled
- [ ] Monitoring configured
- [ ] Backup strategy implemented

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is part of the ZeroWasteAI initiative to reduce food waste through technology innovation.

---

**🌱 Developed with ❤️ by the ZeroWasteAI team to create a more sustainable future through intelligent food management.**

## 📧 Contact

- **Team**: ZeroWasteAI Development Team
- **Mission**: Reducing food waste through AI innovation
- **Vision**: A sustainable future with zero food waste

---

*"Every meal saved is a step towards a more sustainable planet."* 🌍