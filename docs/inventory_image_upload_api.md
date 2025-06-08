# 📤 API de Upload de Imágenes del Inventario

Esta documentación describe el endpoint especializado para subir imágenes específicas del inventario, organizando automáticamente los archivos en carpetas específicas por usuario y tipo de uso.

## 🎯 Propósito

El endpoint permite subir imágenes para diferentes propósitos dentro del inventario:
- **Reconocimiento**: Imágenes para procesos de reconocimiento automático
- **Ingredientes**: Imágenes de ingredientes agregados manualmente
- **Comidas**: Imágenes de comidas preparadas agregadas manualmente

## 🗂️ Estructura de Carpetas

Las imágenes se organizan automáticamente en la siguiente estructura:

```
uploads/
└── {user_uid}/
    ├── recognitions/    # Imágenes para reconocimiento
    └── items/           # Imágenes de ingredientes y comidas manuales
```

---

## 🔧 Endpoint

### Upload de Imagen del Inventario

**POST** `/api/inventory/upload_image`

Sube una imagen específica para el inventario del usuario autenticado.

#### **Headers:**
```http
Authorization: Bearer {jwt_token}
Content-Type: multipart/form-data
```

#### **Form Data:**
| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `image` | File | ✅ | Archivo de imagen (JPG, PNG, GIF, WEBP, max 10MB) |
| `upload_type` | String | ✅ | Tipo de upload: `recognition`, `ingredient`, `food` |
| `item_name` | String | ❌ | Nombre del item (opcional, útil para identificar) |

#### **Valores Válidos para `upload_type`:**
- **`recognition`**: Para imágenes que se usan en reconocimiento automático
- **`ingredient`**: Para imágenes de ingredientes agregados manualmente
- **`food`**: Para imágenes de comidas preparadas agregadas manualmente

---

## 📋 Ejemplos de Uso

### **1. Subir Imagen para Reconocimiento**

```javascript
const uploadRecognitionImage = async (imageFile) => {
  const formData = new FormData();
  formData.append('image', imageFile);
  formData.append('upload_type', 'recognition');
  
  try {
    const response = await fetch('/api/inventory/upload_image', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${userToken}`
      },
      body: formData
    });
    
    if (response.ok) {
      const result = await response.json();
      console.log('✅ Imagen para reconocimiento subida:', result.upload_info.public_url);
      // Se guarda en: uploads/{user_uid}/recognitions/{filename}
      return result;
    }
  } catch (error) {
    console.error('❌ Error subiendo imagen:', error);
  }
};
```

### **2. Subir Imagen de Ingrediente Manual**

```javascript
const uploadIngredientImage = async (imageFile, ingredientName) => {
  const formData = new FormData();
  formData.append('image', imageFile);
  formData.append('upload_type', 'ingredient');
  formData.append('item_name', ingredientName);
  
  try {
    const response = await fetch('/api/inventory/upload_image', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${userToken}`
      },
      body: formData
    });
    
    if (response.ok) {
      const result = await response.json();
      console.log('✅ Imagen de ingrediente subida:', result.upload_info.public_url);
      // Se guarda en: uploads/{user_uid}/items/{filename}
      return result;
    }
  } catch (error) {
    console.error('❌ Error subiendo imagen:', error);
  }
};
```

### **3. Subir Imagen de Comida Manual**

```javascript
const uploadFoodImage = async (imageFile, foodName) => {
  const formData = new FormData();
  formData.append('image', imageFile);
  formData.append('upload_type', 'food');
  formData.append('item_name', foodName);
  
  try {
    const response = await fetch('/api/inventory/upload_image', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${userToken}`
      },
      body: formData
    });
    
    if (response.ok) {
      const result = await response.json();
      console.log('✅ Imagen de comida subida:', result.upload_info.public_url);
      // Se guarda en: uploads/{user_uid}/items/{filename}
      return result;
    }
  } catch (error) {
    console.error('❌ Error subiendo imagen:', error);
  }
};
```

---

## 📥 Respuestas

### **Response Exitoso (201):**

```json
{
  "message": "Inventory image uploaded successfully",
  "upload_info": {
    "storage_path": "uploads/user123/items/a1b2c3d4e5f6.jpg",
    "public_url": "https://storage.googleapis.com/bucket/uploads/user123/items/a1b2c3d4e5f6.jpg",
    "upload_type": "ingredient",
    "folder": "items",
    "user_uid": "user123",
    "item_name": "Tomate",
    "filename": "tomate_photo.jpg"
  }
}
```

### **Response de Error (400):**

```json
{
  "error": "upload_type must be one of: recognition, ingredient, food"
}
```

### **Response de Error (401):**

```json
{
  "error": "JWT token required"
}
```

### **Response de Error (500):**

```json
{
  "error": "Failed to upload inventory image",
  "details": "Storage service unavailable"
}
```

---

## 🛠️ Validaciones

### **Archivo:**
- **Formatos permitidos**: JPG, JPEG, PNG, GIF, WEBP
- **Tamaño máximo**: 10MB
- **Requerido**: Sí

### **Upload Type:**
- **Valores permitidos**: `recognition`, `ingredient`, `food`
- **Requerido**: Sí

### **Item Name:**
- **Longitud mínima**: 2 caracteres (cuando se proporciona)
- **Longitud máxima**: 100 caracteres
- **Requerido**: No (opcional)

---

## 📂 Organización Automática

El sistema organiza automáticamente las imágenes según el `upload_type`:

| Upload Type | Carpeta Final | Propósito |
|-------------|---------------|-----------|
| `recognition` | `uploads/{user_uid}/recognitions/` | Imágenes para reconocimiento automático |
| `ingredient` | `uploads/{user_uid}/items/` | Imágenes de ingredientes manuales |
| `food` | `uploads/{user_uid}/items/` | Imágenes de comidas manuales |

---

## 🔒 Seguridad

- **JWT requerido**: Todas las peticiones requieren token válido
- **Aislamiento por usuario**: Las imágenes se organizan por `user_uid`
- **Validación de tipos**: Solo archivos de imagen permitidos
- **Límite de tamaño**: Máximo 10MB por imagen

---

## 💡 Casos de Uso en Frontend

### **Formulario de Ingrediente Manual:**
```html
<form id="ingredient-form">
  <input type="file" name="image" accept="image/*" required>
  <input type="text" name="ingredient_name" placeholder="Nombre del ingrediente" required>
  <input type="hidden" name="upload_type" value="ingredient">
  <button type="submit">Agregar Ingrediente</button>
</form>
```

### **Formulario de Comida Manual:**
```html
<form id="food-form">
  <input type="file" name="image" accept="image/*" required>
  <input type="text" name="food_name" placeholder="Nombre de la comida" required>
  <input type="hidden" name="upload_type" value="food">
  <button type="submit">Agregar Comida</button>
</form>
```

### **Captura para Reconocimiento:**
```html
<div id="recognition-camera">
  <input type="file" name="image" accept="image/*" capture="camera">
  <input type="hidden" name="upload_type" value="recognition">
  <button onclick="processRecognition()">Reconocer Ingredientes</button>
</div>
```

---

## 🧪 cURL Examples

### **Upload para Reconocimiento:**
```bash
curl -X POST \
  "http://localhost:3000/api/inventory/upload_image" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "image=@path/to/image.jpg" \
  -F "upload_type=recognition"
```

### **Upload de Ingrediente:**
```bash
curl -X POST \
  "http://localhost:3000/api/inventory/upload_image" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "image=@path/to/tomato.jpg" \
  -F "upload_type=ingredient" \
  -F "item_name=Tomate"
```

### **Upload de Comida:**
```bash
curl -X POST \
  "http://localhost:3000/api/inventory/upload_image" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "image=@path/to/pasta.jpg" \
  -F "upload_type=food" \
  -F "item_name=Pasta con Tomate"
```

---

## 🔄 Integración con Otros Endpoints

### **Flujo Completo de Ingrediente Manual:**
1. **Upload imagen**: `POST /api/inventory/upload_image` (upload_type: ingredient)
2. **Agregar al inventario**: `POST /api/inventory/ingredients` (usar public_url)

### **Flujo Completo de Comida Manual:**
1. **Upload imagen**: `POST /api/inventory/upload_image` (upload_type: food)
2. **Agregar al inventario**: `POST /api/inventory/foods` (usar public_url)

### **Flujo de Reconocimiento:**
1. **Upload imagen**: `POST /api/inventory/upload_image` (upload_type: recognition)
2. **Procesar reconocimiento**: `POST /api/recognition/ingredients` (usar public_url)

---

## ⚠️ Consideraciones

### **Nombres de Archivo:**
- Se generan automáticamente usando UUID para evitar conflictos
- El nombre original se preserva en el campo `filename` de la respuesta

### **URLs Públicas:**
- Las imágenes son automáticamente públicas en Firebase Storage
- Usar la `public_url` para mostrar la imagen en el frontend

### **Limpieza:**
- Las imágenes permanecen en storage hasta eliminación manual
- Considerar implementar limpieza automática de imágenes temporales 