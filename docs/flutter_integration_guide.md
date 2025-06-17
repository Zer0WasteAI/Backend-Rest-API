# Guía de Integración Flutter - Sistema de Reconocimiento de Ingredientes

## 🎯 Flujo Completo: Upload + Reconocimiento Asíncrono

### 📱 Dependencias Requeridas

```yaml
dependencies:
  dio: ^5.3.2
  image_picker: ^1.0.4
  flutter_secure_storage: ^9.0.0
```

## 🔄 Flujo de Trabajo Completo

### Paso 1: Configurar el Cliente HTTP

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
    
    // Interceptor para agregar token automáticamente
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
}
```

### Paso 2: Servicio de Upload de Imágenes

```dart
class ImageUploadService {
  final ApiClient _apiClient = ApiClient();

  Future<String> uploadImage(File imageFile, {String imageType = 'ingredient'}) async {
    try {
      print('📤 [FLUTTER] Uploading image: ${imageFile.path}');
      
      // Crear FormData para upload
      FormData formData = FormData.fromMap({
        'image': await MultipartFile.fromFile(
          imageFile.path,
          filename: 'image_${DateTime.now().millisecondsSinceEpoch}.jpg',
          contentType: MediaType('image', 'jpeg'),
        ),
        'item_name': 'scan_${DateTime.now().millisecondsSinceEpoch}',
        'image_type': imageType,
      });

      // Hacer request
      Response response = await _apiClient._dio.post(
        '/image_management/upload_image',
        data: formData,
        options: Options(
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        ),
      );

      if (response.statusCode == 201) {
        final imageUrl = response.data['image']['image_path'];
        print('✅ [FLUTTER] Image uploaded successfully: $imageUrl');
        return imageUrl;
      } else {
        throw Exception('Upload failed with status: ${response.statusCode}');
      }
      
    } catch (e) {
      print('🚨 [FLUTTER] Upload error: $e');
      throw Exception('Error uploading image: $e');
    }
  }

  // Subir múltiples imágenes
  Future<List<String>> uploadMultipleImages(List<File> imageFiles) async {
    List<String> uploadedUrls = [];
    
    for (int i = 0; i < imageFiles.length; i++) {
      print('📤 [FLUTTER] Uploading image ${i + 1}/${imageFiles.length}');
      try {
        String url = await uploadImage(imageFiles[i]);
        uploadedUrls.add(url);
      } catch (e) {
        print('🚨 [FLUTTER] Failed to upload image ${i + 1}: $e');
        rethrow;
      }
    }
    
    return uploadedUrls;
  }
}
```

### Paso 3: Servicio de Reconocimiento Asíncrono

```dart
class RecognitionService {
  final ApiClient _apiClient = ApiClient();

  // Iniciar reconocimiento asíncrono
  Future<String> startAsyncRecognition(List<String> imageUrls) async {
    try {
      print('🚀 [FLUTTER] Starting async recognition with ${imageUrls.length} images');
      
      // ✅ IMPORTANTE: Enviar JSON, NO FormData
      Response response = await _apiClient._dio.post(
        '/recognition/ingredients/async',
        data: {
          'images_paths': imageUrls,  // ✅ Array de strings con URLs
        },
        options: Options(
          headers: {
            'Content-Type': 'application/json',  // ✅ JSON, no multipart/form-data
          },
        ),
      );

      if (response.statusCode == 202) {
        final taskId = response.data['task_id'];
        print('✅ [FLUTTER] Task created successfully: $taskId');
        return taskId;
      } else {
        throw Exception('Recognition failed with status: ${response.statusCode}');
      }
      
    } catch (e) {
      print('🚨 [FLUTTER] Recognition error: $e');
      throw Exception('Error starting recognition: $e');
    }
  }

  // Consultar estado de la tarea
  Future<Map<String, dynamic>> getTaskStatus(String taskId) async {
    try {
      Response response = await _apiClient._dio.get('/recognition/status/$taskId');
      
      if (response.statusCode == 200) {
        return response.data;
      } else {
        throw Exception('Status check failed with status: ${response.statusCode}');
      }
      
    } catch (e) {
      print('🚨 [FLUTTER] Status check error: $e');
      throw Exception('Error checking task status: $e');
    }
  }
}
```

### Paso 4: Controlador Principal

```dart
import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

class IngredientRecognitionController extends ChangeNotifier {
  final ImageUploadService _uploadService = ImageUploadService();
  final RecognitionService _recognitionService = RecognitionService();
  final ImagePicker _picker = ImagePicker();

  // Estados
  bool _isLoading = false;
  bool _isUploading = false;
  bool _isRecognizing = false;
  String _currentStep = '';
  int _progress = 0;
  List<Map<String, dynamic>> _recognizedIngredients = [];
  String? _currentTaskId;
  Timer? _pollingTimer;

  // Getters
  bool get isLoading => _isLoading;
  bool get isUploading => _isUploading;
  bool get isRecognizing => _isRecognizing;
  String get currentStep => _currentStep;
  int get progress => _progress;
  List<Map<String, dynamic>> get recognizedIngredients => _recognizedIngredients;

  // Método principal: Proceso completo
  Future<void> recognizeIngredientsFromCamera() async {
    try {
      // 1. Tomar múltiples fotos
      final List<File> imageFiles = await _selectMultipleImages();
      if (imageFiles.isEmpty) return;

      await _processImages(imageFiles);
      
    } catch (e) {
      print('🚨 [FLUTTER] Recognition process failed: $e');
      _updateState(isLoading: false, step: 'Error: ${e.toString()}');
    }
  }

  // Seleccionar múltiples imágenes
  Future<List<File>> _selectMultipleImages() async {
    final List<XFile> pickedFiles = await _picker.pickMultipleMedia();
    return pickedFiles.map((xFile) => File(xFile.path)).toList();
  }

  // Procesar imágenes completo
  Future<void> _processImages(List<File> imageFiles) async {
    _updateState(isLoading: true, step: 'Iniciando procesamiento...');

    try {
      // Paso 1: Upload de imágenes
      _updateState(isUploading: true, step: 'Subiendo imágenes...');
      final List<String> imageUrls = await _uploadService.uploadMultipleImages(imageFiles);
      
      // Paso 2: Iniciar reconocimiento asíncrono
      _updateState(isUploading: false, isRecognizing: true, step: 'Iniciando reconocimiento...');
      _currentTaskId = await _recognitionService.startAsyncRecognition(imageUrls);
      
      // Paso 3: Iniciar polling
      _startPolling();
      
    } catch (e) {
      _updateState(isLoading: false, step: 'Error: ${e.toString()}');
      rethrow;
    }
  }

  // Polling para consultar estado
  void _startPolling() {
    if (_currentTaskId == null) return;

    _pollingTimer = Timer.periodic(Duration(seconds: 3), (timer) async {
      try {
        final status = await _recognitionService.getTaskStatus(_currentTaskId!);
        
        _updateProgress(
          progress: status['progress_percentage'] ?? 0,
          step: status['current_step'] ?? 'Procesando...',
        );

        // Verificar si completó
        if (status['status'] == 'completed') {
          _handleTaskCompleted(status);
          timer.cancel();
        } else if (status['status'] == 'failed') {
          _handleTaskFailed(status);
          timer.cancel();
        }
        
      } catch (e) {
        print('🚨 [FLUTTER] Polling error: $e');
        timer.cancel();
        _updateState(isLoading: false, step: 'Error consultando estado');
      }
    });
  }

  // Tarea completada
  void _handleTaskCompleted(Map<String, dynamic> status) {
    print('🎉 [FLUTTER] Task completed successfully!');
    
    final resultData = status['result_data'];
    if (resultData != null && resultData['ingredients'] != null) {
      _recognizedIngredients = List<Map<String, dynamic>>.from(resultData['ingredients']);
      print('✅ [FLUTTER] Found ${_recognizedIngredients.length} ingredients');
    }
    
    _updateState(
      isLoading: false, 
      isRecognizing: false, 
      progress: 100,
      step: '¡Reconocimiento completado!'
    );
  }

  // Tarea falló
  void _handleTaskFailed(Map<String, dynamic> status) {
    print('🚨 [FLUTTER] Task failed: ${status['error_message']}');
    _updateState(
      isLoading: false,
      isRecognizing: false,
      step: 'Error: ${status['error_message'] ?? 'Proceso falló'}'
    );
  }

  // Actualizar estado
  void _updateState({
    bool? isLoading,
    bool? isUploading,
    bool? isRecognizing,
    String? step,
    int? progress,
  }) {
    if (isLoading != null) _isLoading = isLoading;
    if (isUploading != null) _isUploading = isUploading;
    if (isRecognizing != null) _isRecognizing = isRecognizing;
    if (step != null) _currentStep = step;
    if (progress != null) _progress = progress;
    notifyListeners();
  }

  void _updateProgress({required int progress, required String step}) {
    _progress = progress;
    _currentStep = step;
    notifyListeners();
  }

  @override
  void dispose() {
    _pollingTimer?.cancel();
    super.dispose();
  }
}
```

### Paso 5: Widget de UI

```dart
class IngredientRecognitionScreen extends StatefulWidget {
  @override
  _IngredientRecognitionScreenState createState() => _IngredientRecognitionScreenState();
}

class _IngredientRecognitionScreenState extends State<IngredientRecognitionScreen> {
  late IngredientRecognitionController _controller;

  @override
  void initState() {
    super.initState();
    _controller = IngredientRecognitionController();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Reconocimiento de Ingredientes')),
      body: ChangeNotifierProvider.value(
        value: _controller,
        child: Consumer<IngredientRecognitionController>(
          builder: (context, controller, child) {
            return Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                children: [
                  // Botón principal
                  ElevatedButton(
                    onPressed: controller.isLoading ? null : () {
                      controller.recognizeIngredientsFromCamera();
                    },
                    child: Text('Reconocer Ingredientes'),
                  ),
                  
                  SizedBox(height: 20),
                  
                  // Indicador de progreso
                  if (controller.isLoading) ...[
                    LinearProgressIndicator(
                      value: controller.progress / 100,
                    ),
                    SizedBox(height: 10),
                    Text(
                      '${controller.progress}% - ${controller.currentStep}',
                      textAlign: TextAlign.center,
                    ),
                  ],
                  
                  SizedBox(height: 20),
                  
                  // Lista de ingredientes reconocidos
                  Expanded(
                    child: ListView.builder(
                      itemCount: controller.recognizedIngredients.length,
                      itemBuilder: (context, index) {
                        final ingredient = controller.recognizedIngredients[index];
                        return Card(
                          child: ListTile(
                            leading: ingredient['image_path'] != null
                                ? Image.network(
                                    ingredient['image_path'],
                                    width: 50,
                                    height: 50,
                                    fit: BoxFit.cover,
                                  )
                                : Icon(Icons.image_not_supported),
                            title: Text(ingredient['name'] ?? 'Sin nombre'),
                            subtitle: Text(
                              'Cantidad: ${ingredient['quantity'] ?? 'N/A'}\n'
                              'Vence: ${ingredient['expiration_date'] ?? 'N/A'}',
                            ),
                          ),
                        );
                      },
                    ),
                  ),
                ],
              ),
            );
          },
        ),
      ),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }
}
```

## 🔍 Debugging y Logs

### En Flutter, puedes agregar logs para debugging:

```dart
void _logRequest(String endpoint, dynamic data) {
  print('📱 [FLUTTER REQUEST] $endpoint');
  print('📱 [FLUTTER DATA] $data');
}

void _logResponse(String endpoint, Response response) {
  print('📱 [FLUTTER RESPONSE] $endpoint - ${response.statusCode}');
  print('📱 [FLUTTER BODY] ${response.data}');
}
```

## ⚠️ Puntos Críticos

### ✅ LO QUE DEBE SER ASÍ:

1. **Upload de imágenes:**
   - `Content-Type: multipart/form-data`
   - `FormData` con archivo
   - Endpoint: `/image_management/upload_image`

2. **Reconocimiento asíncrono:**
   - `Content-Type: application/json`
   - `JSON` con array de URLs
   - Endpoint: `/recognition/ingredients/async`

### ❌ ERRORES COMUNES:

1. ❌ Enviar archivos al endpoint async
2. ❌ Usar FormData para el endpoint async
3. ❌ No hacer polling para consultar estado
4. ❌ No manejar los diferentes estados de la tarea

## 🎯 Resumen del Flujo

```
📱 Usuario selecciona imágenes
   ↓
📤 Upload imágenes individualmente → URLs
   ↓
🚀 Enviar URLs al reconocimiento async → task_id
   ↓
🔄 Polling cada 3 segundos consultando estado
   ↓
✅ Estado = 'completed' → Mostrar ingredientes con imágenes
```

¡Con esta guía, el equipo de Flutter debería poder integrar perfectamente el sistema! 🚀 