# 🔐 Authentication Architecture

## 🎯 Overview
ZeroWasteAI uses a **clean authentication architecture** with **Firebase Authentication** + **JWT tokens**, eliminating unnecessary OAuth, SMS, and email dependencies for a streamlined, secure system.

## 🏗️ Authentication Flow

### **1. Firebase Authentication**
```
User → Firebase Auth → Firebase ID Token → Backend Validation
```

### **2. JWT Token Management**  
```
Valid Firebase Token → JWT Generation → API Access → Token Blacklisting
```

## 🔧 Architecture Components

### **Core Authentication Infrastructure**

#### **🔥 Firebase Integration (`src/infrastructure/firebase/`)**
```
firebase_storage_adapter.py    # Firebase Storage integration
image_loader_service.py        # Image handling service
```

#### **🔐 JWT Security (`src/infrastructure/auth/`)**
```
jwt_callbacks.py               # JWT security callbacks
jwt_service.py                 # JWT token management
```

#### **🛡️ Security Middleware (`src/infrastructure/security/`)**
```
security_headers.py            # HTTP security headers
```

### **Database Security Tables**
```sql
auth_users                     # Firebase UID mapping
token_blacklist               # Revoked JWT tokens  
refresh_token_tracking        # Session management
```

## 🔄 Authentication Process

### **User Registration/Login**
1. **Frontend** → Firebase Authentication
2. **Firebase** returns ID token
3. **Backend** validates Firebase ID token
4. **Backend** creates/updates local user record
5. **Backend** issues JWT access token
6. **Client** uses JWT for API calls

### **Secure Logout**
1. **Client** sends logout request with JWT
2. **Backend** adds JWT to blacklist
3. **Backend** invalidates refresh tokens
4. **Client** clears local tokens

### **Token Refresh**
1. **Client** sends refresh token
2. **Backend** validates refresh token
3. **Backend** issues new JWT token
4. **Backend** updates refresh token tracking

## 🛡️ Security Features

### **Enhanced JWT Security**
- **Token blacklisting** for secure logout
- **Refresh token tracking** for session management
- **Configurable token expiration**
- **Security callbacks** for validation

### **Firebase Integration Benefits**
- **Multi-platform support** (web, mobile)
- **Social login options** (Google, etc.)
- **Built-in security features**
- **Scalable user management**

### **Security Headers**
- Content Security Policy (CSP)
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- Strict-Transport-Security
- X-XSS-Protection

## 📦 Cleaned Dependencies

### **✅ Kept (Essential)**
```python
firebase-admin==6.8.0         # Firebase integration
Flask-JWT-Extended==4.7.1     # JWT management
bcrypt==4.3.0                  # Password hashing
cryptography==44.0.2          # Security utilities
```

### **❌ Removed (Unnecessary)**
```python
# OAuth libraries (using Firebase instead)
Authlib==1.5.2                

# Email services (not needed)
email_validator==2.2.0        
secure-smtplib==0.1.1         

# SMS services (not needed)
twilio==9.5.2                 
```

## 🔌 API Endpoints

### **Authentication Endpoints (`/api/auth`)**
```
POST /api/auth/firebase-login   # Firebase token validation
POST /api/auth/logout          # Secure logout with blacklisting
POST /api/auth/refresh         # Token refresh
GET  /api/auth/verify          # Token validation
```

### **Security Headers**
All API responses include:
```http
Content-Security-Policy: default-src 'self'
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-XSS-Protection: 1; mode=block
```

## 🔧 Configuration

### **Environment Variables**
```bash
# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=src/config/firebase_credentials.json
FIREBASE_STORAGE_BUCKET=your-bucket.firebasestorage.app

# JWT Configuration  
JWT_SECRET_KEY=your-secret-key
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=2592000

# Security
FLASK_ENV=production
SECRET_KEY=your-flask-secret
```

### **Firebase Setup**
1. Create Firebase project
2. Enable Authentication
3. Configure providers (Email/Password, Google, etc.)
4. Download service account credentials
5. Place in `src/config/firebase_credentials.json`

## 🧪 Testing Authentication

### **Firebase Token Validation**
```bash
# Test Firebase login
curl -X POST http://localhost:3000/api/auth/firebase-login \
  -H "Content-Type: application/json" \
  -d '{"firebase_token": "your_firebase_id_token"}'
```

### **JWT Token Usage**
```bash
# Use JWT for protected endpoints
curl -X GET http://localhost:3000/api/user/profile \
  -H "Authorization: Bearer your_jwt_token"
```

### **Secure Logout**
```bash
# Logout with token blacklisting
curl -X POST http://localhost:3000/api/auth/logout \
  -H "Authorization: Bearer your_jwt_token"
```

## 🚀 Benefits of Clean Architecture

### **✅ Advantages**
- **Simplified Dependencies** - Only essential packages
- **Better Performance** - Reduced overhead
- **Enhanced Security** - Firebase + JWT security
- **Easier Maintenance** - Less complexity
- **Mobile Ready** - Firebase native support
- **Scalable** - Firebase handles user management

### **🎯 Focus Areas**
- **Core Functionality** - Food recognition & inventory
- **User Experience** - Streamlined authentication
- **Performance** - Optimized for speed
- **Security** - Enterprise-grade protection

## 📋 Migration Notes

### **From Previous Architecture**
- **Removed OAuth complexity** - Firebase handles providers
- **Eliminated email services** - Not needed for core functionality  
- **Removed SMS integration** - Simplified authentication flow
- **Kept JWT security** - Enhanced with blacklisting
- **Maintained Firebase** - Core authentication system

### **Backward Compatibility**
- **API endpoints unchanged** - Same interface
- **Database schema preserved** - Existing data safe
- **Security enhanced** - Additional protection layers
- **Performance improved** - Reduced dependencies

---

**🔐 This clean authentication architecture provides enterprise-grade security while maintaining simplicity and performance for the ZeroWasteAI platform.**