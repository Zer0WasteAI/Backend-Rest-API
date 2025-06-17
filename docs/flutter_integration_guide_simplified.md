# 📱 Guía de Integración Flutter - Reconocimiento Simplificado

## 🎯 **Nuevo Flujo Simplificado**

### ✨ **Ventajas del Enfoque Simplificado**
- 🚀 **Respuesta inmediata** con todos los datos de ingredientes
- 🎨 **Generación de imágenes en background** sin polling complejo
- 📱 **Implementación frontend simple** 
- 🔄 **Verificación periódica** opcional de imágenes

### 🔄 **Flujo de Trabajo**

1. **Upload de Imágenes** → Obtener URLs firmadas
2. **Llamar Reconocimiento** → Respuesta inmediata con datos completos
   - 🥗 **Ingredientes**: `/api/recognition/ingredients`
   - 🍽️ **Comidas**: `/api/recognition/foods`
3. **Verificar Imágenes** → Periódicamente hasta que estén listas
4. **Actualizar UI** → Mostrar imágenes reales cuando estén disponibles

---

## 📋 **Implementación Flutter**

### 1️⃣ **Dependencias**

```yaml
dependencies:
  dio: ^5.3.2
  image_picker: ^1.0.4
  flutter_secure_storage: ^9.0.0
```

### 2️⃣ **Cliente API Base**

```dart
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiClient {
  static const String baseUrl = 'http://127.0.0.1:3000/api';
  final Dio _dio = Dio();
  final FlutterSecureStorage _storage = FlutterSecureStorage();

  ApiClient() {
    _dio.options.baseUrl = baseUrl;
    _dio.options.connectTimeout = Duration(seconds: 30);
    _dio.options.receiveTimeout = Duration(seconds: 30);
    
    // Auto-agregar token
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _storage.read(key: 'auth_token');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
    ));
  }

  Dio get dio => _dio;
}
```

### 3️⃣ **Servicio de Upload (Sin cambios)**

```dart
class ImageUploadService {
  final ApiClient _apiClient = ApiClient();

  Future<String> uploadImage(File imageFile, {String imageType = 'ingredient'}) async {
    try {
      print('📤 [UPLOAD] Uploading: ${imageFile.path}');
      
      FormData formData = FormData.fromMap({
        'image': await MultipartFile.fromFile(
          imageFile.path,
          filename: 'image_${DateTime.now().millisecondsSinceEpoch}.jpg',
        ),
        'item_name': 'scan_${DateTime.now().millisecondsSinceEpoch}',
        'image_type': imageType,
      });

      Response response = await _apiClient.dio.post(
        '/image_management/upload_image',
        data: formData,
        options: Options(headers: {'Content-Type': 'multipart/form-data'}),
      );

      if (response.statusCode == 201) {
        String imageUrl = response.data['image']['image_path'];
        print('✅ [UPLOAD] Success: $imageUrl');
        return imageUrl;
      } else {
        throw Exception('Upload failed: ${response.statusCode}');
      }
      
    } catch (e) {
      print('🚨 [UPLOAD] Error: $e');
      throw Exception('Upload error: $e');
    }
  }

  Future<List<String>> uploadMultipleImages(List<File> images) async {
    List<String> urls = [];
    for (int i = 0; i < images.length; i++) {
      print('📤 Uploading ${i + 1}/${images.length}');
      String url = await uploadImage(images[i]);
      urls.add(url);
    }
    return urls;
  }
}
```

### 4️⃣ **Servicio de Reconocimiento Simplificado**

```dart
class SimplifiedRecognitionService {
  final ApiClient _apiClient = ApiClient();

  // ✨ NUEVO: Reconocimiento de ingredientes con respuesta inmediata
  Future<RecognitionResult> recognizeIngredients(List<String> imageUrls) async {
    try {
      print('🥗 [INGREDIENTS] Starting with ${imageUrls.length} images');
      
      Response response = await _apiClient.dio.post(
        '/recognition/ingredients',  // ✨ Endpoint simplificado
        data: {'images_paths': imageUrls},
        options: Options(headers: {'Content-Type': 'application/json'}),
      );

      if (response.statusCode == 200) {
        return RecognitionResult.fromJson(response.data);
      } else {
        throw Exception('Recognition failed: ${response.statusCode}');
      }
      
    } catch (e) {
      print('🚨 [INGREDIENTS] Error: $e');
      throw Exception('Recognition error: $e');
    }
  }

  // ✨ NUEVO: Reconocimiento de comidas con respuesta inmediata
  Future<FoodRecognitionResult> recognizeFoods(List<String> imageUrls) async {
    try {
      print('🍽️ [FOODS] Starting with ${imageUrls.length} images');
      
      Response response = await _apiClient.dio.post(
        '/recognition/foods',  // ✨ Endpoint simplificado para comidas
        data: {'images_paths': imageUrls},
        options: Options(headers: {'Content-Type': 'application/json'}),
      );

      if (response.statusCode == 200) {
        return FoodRecognitionResult.fromJson(response.data);
      } else {
        throw Exception('Food recognition failed: ${response.statusCode}');
      }
      
    } catch (e) {
      print('🚨 [FOODS] Error: $e');
      throw Exception('Food recognition error: $e');
    }
  }

  // ✨ NUEVO: Verificar estado de imágenes
  Future<ImageStatus> checkImagesStatus(String recognitionId) async {
    try {
      Response response = await _apiClient.dio.get(
        '/recognition/$recognitionId/images'
      );

      if (response.statusCode == 200) {
        return ImageStatus.fromJson(response.data);
      } else {
        throw Exception('Status check failed: ${response.statusCode}');
      }
      
    } catch (e) {
      print('🚨 [IMAGES] Status check error: $e');
      throw Exception('Status check error: $e');
    }
  }
}
```

### 5️⃣ **Modelos de Datos**

```dart
class RecognitionResult {
  final String recognitionId;
  final List<Ingredient> ingredients;
  final String imagesStatus;
  final String message;

  RecognitionResult({
    required this.recognitionId,
    required this.ingredients,
    required this.imagesStatus,
    required this.message,
  });

  factory RecognitionResult.fromJson(Map<String, dynamic> json) {
    return RecognitionResult(
      recognitionId: json['recognition_id'],
      ingredients: (json['ingredients'] as List)
          .map((i) => Ingredient.fromJson(i))
          .toList(),
      imagesStatus: json['images_status'] ?? 'generating_in_background',
      message: json['message'],
    );
  }
}

class FoodRecognitionResult {
  final String recognitionId;
  final List<Food> foods;
  final String imagesStatus;
  final String message;

  FoodRecognitionResult({
    required this.recognitionId,
    required this.foods,
    required this.imagesStatus,
    required this.message,
  });

  factory FoodRecognitionResult.fromJson(Map<String, dynamic> json) {
    return FoodRecognitionResult(
      recognitionId: json['recognition_id'],
      foods: (json['foods'] as List)
          .map((f) => Food.fromJson(f))
          .toList(),
      imagesStatus: json['images_status'] ?? 'generating_in_background',
      message: json['message'],
    );
  }
}

class Ingredient {
  final String name;
  final String description;
  final int quantity;
  final String typeUnit;
  final String storageType;
  final String expirationDate;
  final String addedAt;
  String imagePath;  // Puede cambiar cuando se genere
  String imageStatus; // 'generating' → 'ready'
  final bool? allergyAlert;
  final List<String>? allergens;

  Ingredient({
    required this.name,
    required this.description,
    required this.quantity,
    required this.typeUnit,
    required this.storageType,
    required this.expirationDate,
    required this.addedAt,
    required this.imagePath,
    required this.imageStatus,
    this.allergyAlert,
    this.allergens,
  });

  factory Ingredient.fromJson(Map<String, dynamic> json) {
    return Ingredient(
      name: json['name'],
      description: json['description'] ?? '',
      quantity: json['quantity'] ?? 0,
      typeUnit: json['type_unit'] ?? '',
      storageType: json['storage_type'] ?? '',
      expirationDate: json['expiration_date'] ?? '',
      addedAt: json['added_at'] ?? '',
      imagePath: json['image_path'] ?? '',
      imageStatus: json['image_status'] ?? 'generating',
      allergyAlert: json['allergy_alert'],
      allergens: json['allergens']?.cast<String>(),
    );
  }
}

class Food {
  final String name;
  final String description;
  final List<String> mainIngredients;
  final String category;
  final double? calories;
  final String storageType;
  final int expirationTime;
  final String timeUnit;
  final String expirationDate;
  final String addedAt;
  String imagePath;  // Puede cambiar cuando se genere
  final bool? allergyAlert;
  final List<String>? allergens;

  Food({
    required this.name,
    required this.description,
    required this.mainIngredients,
    required this.category,
    this.calories,
    required this.storageType,
    required this.expirationTime,
    required this.timeUnit,
    required this.expirationDate,
    required this.addedAt,
    required this.imagePath,
    this.allergyAlert,
    this.allergens,
  });

  factory Food.fromJson(Map<String, dynamic> json) {
    return Food(
      name: json['name'],
      description: json['description'] ?? '',
      mainIngredients: (json['main_ingredients'] as List?)?.cast<String>() ?? [],
      category: json['category'] ?? '',
      calories: json['calories']?.toDouble(),
      storageType: json['storage_type'] ?? '',
      expirationTime: json['expiration_time'] ?? 3,
      timeUnit: json['time_unit'] ?? 'days',
      expirationDate: json['expiration_date'] ?? '',
      addedAt: json['added_at'] ?? '',
      imagePath: json['image_path'] ?? '',
      allergyAlert: json['allergy_alert'],
      allergens: json['allergens']?.cast<String>(),
    );
  }
}

class ImageStatus {
  final String recognitionId;
  final String imagesStatus;
  final int imagesReady;
  final int imagesGenerating;
  final int totalIngredients;
  final int progressPercentage;
  final List<Ingredient> ingredients;
  final String message;

  ImageStatus({
    required this.recognitionId,
    required this.imagesStatus,
    required this.imagesReady,
    required this.imagesGenerating,
    required this.totalIngredients,
    required this.progressPercentage,
    required this.ingredients,
    required this.message,
  });

  factory ImageStatus.fromJson(Map<String, dynamic> json) {
    return ImageStatus(
      recognitionId: json['recognition_id'],
      imagesStatus: json['images_status'],
      imagesReady: json['images_ready'],
      imagesGenerating: json['images_generating'],
      totalIngredients: json['total_ingredients'],
      progressPercentage: json['progress_percentage'],
      ingredients: (json['ingredients'] as List)
          .map((i) => Ingredient.fromJson(i))
          .toList(),
      message: json['message'],
    );
  }
}
```

### 6️⃣ **Controlador Simplificado**

```dart
import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

class SimplifiedRecognitionController extends ChangeNotifier {
  final ImageUploadService _uploadService = ImageUploadService();
  final SimplifiedRecognitionService _recognitionService = SimplifiedRecognitionService();
  final ImagePicker _picker = ImagePicker();

  // Estados
  bool _isLoading = false;
  String _currentStep = '';
  RecognitionResult? _recognitionResult;
  Timer? _imageCheckTimer;

  // Getters
  bool get isLoading => _isLoading;
  String get currentStep => _currentStep;
  RecognitionResult? get recognitionResult => _recognitionResult;
  List<Ingredient> get ingredients => _recognitionResult?.ingredients ?? [];

  // ✨ MÉTODO PRINCIPAL SIMPLIFICADO PARA INGREDIENTES
  Future<void> recognizeIngredientsFromCamera() async {
    try {
      _setLoading(true, 'Seleccionando imágenes...');
      
      // 1. Seleccionar múltiples imágenes
      final List<XFile> pickedFiles = await _picker.pickMultipleMedia(
        limit: 5,
        imageQuality: 80,
      );

      if (pickedFiles.isEmpty) {
        _setLoading(false, '');
        return;
      }

      List<File> imageFiles = pickedFiles.map((xFile) => File(xFile.path)).toList();
      
      // 2. Upload de imágenes
      _setLoading(true, 'Subiendo ${imageFiles.length} imágenes...');
      List<String> imageUrls = await _uploadService.uploadMultipleImages(imageFiles);
      
      // 3. ✨ Reconocimiento con respuesta inmediata
      _setLoading(true, 'Reconociendo ingredientes...');
      _recognitionResult = await _recognitionService.recognizeIngredients(imageUrls);
      
      _setLoading(false, '');
      notifyListeners();
      
      // 4. ✨ Verificar imágenes en background (opcional)
      if (_recognitionResult!.imagesStatus == 'generating_in_background') {
        _startImagePolling(_recognitionResult!.recognitionId);
      }
      
    } catch (e) {
      _setLoading(false, '');
      print('🚨 Ingredients recognition error: $e');
      // Manejar error
    }
  }

  // ✨ NUEVO: MÉTODO SIMPLIFICADO PARA COMIDAS
  Future<void> recognizeFoodsFromCamera() async {
    try {
      _setLoading(true, 'Seleccionando imágenes de comidas...');
      
      // 1. Seleccionar múltiples imágenes
      final List<XFile> pickedFiles = await _picker.pickMultipleMedia(
        limit: 3,
        imageQuality: 80,
      );

      if (pickedFiles.isEmpty) {
        _setLoading(false, '');
        return;
      }

      List<File> imageFiles = pickedFiles.map((xFile) => File(xFile.path)).toList();
      
      // 2. Upload de imágenes
      _setLoading(true, 'Subiendo ${imageFiles.length} imágenes...');
      List<String> imageUrls = await _uploadService.uploadMultipleImages(imageFiles);
      
      // 3. ✨ Reconocimiento de comidas con respuesta inmediata
      _setLoading(true, 'Reconociendo comidas...');
      FoodRecognitionResult foodResult = await _recognitionService.recognizeFoods(imageUrls);
      
      _setLoading(false, '');
      
      // 🍽️ Mostrar resultado de comidas (puedes adaptarlo a tu UI)
      print('✅ Recognized ${foodResult.foods.length} foods');
      for (Food food in foodResult.foods) {
        print('🍽️ ${food.name}: ${food.description}');
      }
      
      notifyListeners();
      
      // 4. ✨ Las imágenes se generan automáticamente en background
      print('🎨 Food images generating in background for: ${foodResult.recognitionId}');
      
    } catch (e) {
      _setLoading(false, '');
      print('🚨 Food recognition error: $e');
      // Manejar error
    }
  }

  // ✨ VERIFICACIÓN OPCIONAL DE IMÁGENES
  void _startImagePolling(String recognitionId) {
    print('🎨 Starting image polling for: $recognitionId');
    
    _imageCheckTimer = Timer.periodic(Duration(seconds: 5), (timer) async {
      try {
        ImageStatus status = await _recognitionService.checkImagesStatus(recognitionId);
        
        if (status.imagesStatus == 'ready') {
          print('✅ All images ready!');
          
          // Actualizar ingredientes con nuevas imágenes
          _recognitionResult = RecognitionResult(
            recognitionId: _recognitionResult!.recognitionId,
            ingredients: status.ingredients,
            imagesStatus: 'ready',
            imagesCheckUrl: _recognitionResult!.imagesCheckUrl,
            message: '✅ Imágenes listas',
          );
          
          notifyListeners();
          timer.cancel();
        } else {
          print('🎨 Images progress: ${status.progressPercentage}%');
        }
        
      } catch (e) {
        print('🚨 Image polling error: $e');
        timer.cancel();
      }
    });
  }

  void _setLoading(bool loading, String step) {
    _isLoading = loading;
    _currentStep = step;
    notifyListeners();
  }

  @override
  void dispose() {
    _imageCheckTimer?.cancel();
    super.dispose();
  }
}
```

### 7️⃣ **Widget de UI Simplificado**

```dart
class SimplifiedRecognitionScreen extends StatefulWidget {
  @override
  _SimplifiedRecognitionScreenState createState() => _SimplifiedRecognitionScreenState();
}

class _SimplifiedRecognitionScreenState extends State<SimplifiedRecognitionScreen> {
  late SimplifiedRecognitionController _controller;

  @override
  void initState() {
    super.initState();
    _controller = SimplifiedRecognitionController();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Reconocimiento Simplificado')),
      body: ListenableBuilder(
        listenable: _controller,
        builder: (context, _) {
          if (_controller.isLoading) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 16),
                  Text(_controller.currentStep),
                ],
              ),
            );
          }

          if (_controller.ingredients.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.camera_alt, size: 64, color: Colors.grey),
                  SizedBox(height: 16),
                  Text('¡Reconoce con IA!', style: TextStyle(fontSize: 18)),
                  SizedBox(height: 32),
                  
                  // 🥗 Botón para Ingredientes
                  ElevatedButton.icon(
                    onPressed: _controller.recognizeIngredientsFromCamera,
                    icon: Icon(Icons.grass),
                    label: Text('Reconocer Ingredientes'),
                    style: ElevatedButton.styleFrom(
                      padding: EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                      backgroundColor: Colors.green,
                      foregroundColor: Colors.white,
                    ),
                  ),
                  
                  SizedBox(height: 16),
                  
                  // 🍽️ Botón para Comidas
                  ElevatedButton.icon(
                    onPressed: _controller.recognizeFoodsFromCamera,
                    icon: Icon(Icons.restaurant),
                    label: Text('Reconocer Comidas'),
                    style: ElevatedButton.styleFrom(
                      padding: EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                      backgroundColor: Colors.orange,
                      foregroundColor: Colors.white,
                    ),
                  ),
                  
                  SizedBox(height: 24),
                  Text(
                    'Selecciona el tipo de reconocimiento que necesitas',
                    style: TextStyle(color: Colors.grey.shade600),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            );
          }

          // ✨ Mostrar resultados inmediatamente
          return Column(
            children: [
              if (_controller.recognitionResult?.imagesStatus == 'generating')
                Container(
                  padding: EdgeInsets.all(16),
                  color: Colors.blue.shade50,
                  child: Row(
                    children: [
                      SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                      SizedBox(width: 12),
                      Text('🎨 Generando imágenes en segundo plano...'),
                    ],
                  ),
                ),
              
              Expanded(
                child: ListView.builder(
                  itemCount: _controller.ingredients.length,
                  itemBuilder: (context, index) {
                    final ingredient = _controller.ingredients[index];
                    return IngredientCard(ingredient: ingredient);
                  },
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }
}

class IngredientCard extends StatelessWidget {
  final Ingredient ingredient;

  const IngredientCard({Key? key, required this.ingredient}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.all(8),
      child: ListTile(
        leading: ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: Image.network(
            ingredient.imagePath,
            width: 60,
            height: 60,
            fit: BoxFit.cover,
            errorBuilder: (context, error, stackTrace) {
              return Container(
                width: 60,
                height: 60,
                color: Colors.grey.shade300,
                child: Icon(Icons.image_not_supported),
              );
            },
            loadingBuilder: (context, child, loadingProgress) {
              if (loadingProgress == null) return child;
              return Container(
                width: 60,
                height: 60,
                color: Colors.grey.shade300,
                child: Center(
                  child: CircularProgressIndicator(
                    value: loadingProgress.expectedTotalBytes != null
                        ? loadingProgress.cumulativeBytesLoaded / 
                          loadingProgress.expectedTotalBytes!
                        : null,
                  ),
                ),
              );
            },
          ),
        ),
        title: Text(ingredient.name),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('${ingredient.quantity} ${ingredient.typeUnit}'),
            Text('Vence: ${_formatDate(ingredient.expirationDate)}'),
            if (ingredient.allergyAlert == true)
              Container(
                padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.red.shade100,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  '⚠️ Alergia',
                  style: TextStyle(color: Colors.red.shade800, fontSize: 12),
                ),
              ),
          ],
        ),
        trailing: ingredient.imageStatus == 'generating' 
            ? Icon(Icons.hourglass_empty, color: Colors.orange)
            : Icon(Icons.check_circle, color: Colors.green),
      ),
    );
  }

  String _formatDate(String isoDate) {
    try {
      DateTime date = DateTime.parse(isoDate);
      return '${date.day}/${date.month}/${date.year}';
    } catch (e) {
      return isoDate;
    }
  }
}
```

---

## 🎯 **Resumen del Flujo Simplificado**

### ✅ **Lo que Hace el Frontend**
1. **Upload de imágenes** (igual que antes)
2. **Llamar endpoint correspondiente**:
   - 🥗 `/recognition/ingredients` (ingredientes)
   - 🍽️ `/recognition/foods` (comidas)
3. **Mostrar datos inmediatamente** (con placeholders de imagen)
4. **Verificar imágenes periódicamente** con `/recognition/{id}/images` (opcional)
5. **Actualizar UI** cuando las imágenes estén listas

### ✅ **Lo que Hace el Backend**
1. **Responde inmediatamente** con todos los datos de reconocimiento
2. **Genera imágenes en background** automáticamente (sin task tracking complejo)
3. **Actualiza la base de datos** cuando las imágenes están listas
4. **Logs claros** para debuggear todo el proceso

### 🎉 **Ventajas**
- 📱 **Frontend más simple** - No necesita manejar task_id ni polling complejo
- 🚀 **Respuesta inmediata** - El usuario ve resultados al instante
- 🎨 **Imágenes automáticas** - Se actualizan transparentemente en background
- 🥗🍽️ **Doble funcionalidad** - Ingredientes y comidas con el mismo flujo
- 🐛 **Más fácil de debuggear** - Logs claros del proceso
- ⚡ **Más rápido** - Sin polling innecesario, imágenes opcionales

¡Esta implementación es mucho más simple, eficiente y flexible! 🚀

### 🔧 **Endpoints Disponibles**

| Endpoint | Método | Descripción | Respuesta |
|----------|---------|-------------|-----------|
| `/api/recognition/ingredients` | POST | Reconocimiento simplificado de ingredientes | Datos inmediatos + imágenes en background |
| `/api/recognition/foods` | POST | Reconocimiento simplificado de comidas | Datos inmediatos + imágenes en background |
| `/api/recognition/{id}/images` | GET | Verificar estado de imágenes (opcional) | Estado actualizado con imágenes |
| `/api/image_management/upload_image` | POST | Upload de imágenes individuales | URL firmada |

### 📋 **Formato de Request**
```json
{
  "images_paths": [
    "https://storage.googleapis.com/bucket/path/image1.jpg?...",
    "https://storage.googleapis.com/bucket/path/image2.jpg?..."
  ]
}
```

### 📄 **Formato de Response (Ingredientes)**
```json
{
  "recognition_id": "abc123...",
  "ingredients": [
    {
      "name": "Tomate",
      "description": "Tomate rojo maduro",
      "quantity": 3,
      "type_unit": "unidad",
      "storage_type": "Refrigerator",
      "expiration_date": "2025-06-24T10:16:20Z",
      "added_at": "2025-06-17T10:16:20Z",
      "image_path": null,
      "allergy_alert": false
    }
  ],
  "images_status": "generating_in_background",
  "message": "✅ Ingredientes reconocidos exitosamente. Las imágenes se están generando automáticamente."
}
```

### 📄 **Formato de Response (Comidas)**
```json
{
  "recognition_id": "def456...",
  "foods": [
    {
      "name": "Pizza Margherita",
      "description": "Pizza con tomate, mozzarella y albahaca",
      "main_ingredients": ["tomate", "mozzarella", "albahaca"],
      "category": "Italian",
      "calories": 250,
      "storage_type": "Refrigerator",
      "expiration_time": 3,
      "time_unit": "days",
      "expiration_date": "2025-06-20T10:16:20Z",
      "added_at": "2025-06-17T10:16:20Z",
      "image_path": null,
      "allergy_alert": false
    }
  ],
  "images_status": "generating_in_background",
  "message": "✅ Comidas reconocidas exitosamente. Las imágenes se están generando automáticamente."
}
``` 