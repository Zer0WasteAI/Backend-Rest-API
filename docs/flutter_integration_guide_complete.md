# 🚀 **Guía Completa Flutter - Nuevos Endpoints ZeroWasteAI**

## 📊 **RESUMEN DE NUEVOS ENDPOINTS**

### 1. **🍽️ Endpoint: Agregar Comidas desde Reconocimiento**
- **URL**: `POST /api/inventory/foods/from-recognition`
- **Propósito**: Agregar comidas al inventario desde reconocimiento IA
- **Estado**: ✅ **IMPLEMENTADO Y FUNCIONAL**

### 2. **📚 Endpoint: Recetas por Defecto**
- **URL**: `GET /api/recipes/default`
- **Propósito**: Obtener 15 recetas curadas con imágenes de alta calidad
- **Estado**: ✅ **IMPLEMENTADO Y FUNCIONAL**

---

## 🍽️ **1. ENDPOINT: AGREGAR COMIDAS DESDE RECONOCIMIENTO**

### **📋 Información Técnica**
```dart
// URL del endpoint
static const String FOODS_FROM_RECOGNITION_URL = '/api/inventory/foods/from-recognition';

// Método HTTP
static const String METHOD = 'POST';

// Headers requeridos
Map<String, String> headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer $jwt_token', // ⚠️ REQUIERE AUTENTICACIÓN
};
```

### **📦 Estructura de Request**
```dart
class FoodsFromRecognitionRequest {
  final List<FoodRecognitionData> foods;

  FoodsFromRecognitionRequest({required this.foods});

  Map<String, dynamic> toJson() => {
    'foods': foods.map((food) => food.toJson()).toList(),
  };
}

class FoodRecognitionData {
  final String name;
  final String description;
  final List<String> mainIngredients;
  final String category;
  final String storageType;
  final int expirationTime;
  final String timeUnit;
  final String tips;
  final int servingQuantity;
  final int? calories;
  final String? imagePath;

  FoodRecognitionData({
    required this.name,
    required this.description,
    required this.mainIngredients,
    required this.category,
    required this.storageType,
    required this.expirationTime,
    required this.timeUnit,
    required this.tips,
    required this.servingQuantity,
    this.calories,
    this.imagePath,
  });

  Map<String, dynamic> toJson() => {
    'name': name,
    'description': description,
    'main_ingredients': mainIngredients,
    'category': category,
    'storage_type': storageType,
    'expiration_time': expirationTime,
    'time_unit': timeUnit,
    'tips': tips,
    'serving_quantity': servingQuantity,
    if (calories != null) 'calories': calories,
    if (imagePath != null) 'image_path': imagePath,
  };
}
```

### **📨 Estructura de Response**
```dart
class FoodsFromRecognitionResponse {
  final bool success;
  final String message;
  final List<EnrichedFoodData> enrichedFoods;
  final int totalProcessed;
  final int successfullyAdded;
  final List<String> errors;

  FoodsFromRecognitionResponse({
    required this.success,
    required this.message,
    required this.enrichedFoods,
    required this.totalProcessed,
    required this.successfullyAdded,
    required this.errors,
  });

  factory FoodsFromRecognitionResponse.fromJson(Map<String, dynamic> json) {
    return FoodsFromRecognitionResponse(
      success: json['success'] ?? false,
      message: json['message'] ?? '',
      enrichedFoods: (json['enriched_foods'] as List<dynamic>?)
          ?.map((item) => EnrichedFoodData.fromJson(item))
          .toList() ?? [],
      totalProcessed: json['total_processed'] ?? 0,
      successfullyAdded: json['successfully_added'] ?? 0,
      errors: List<String>.from(json['errors'] ?? []),
    );
  }
}

class EnrichedFoodData {
  final String name;
  final String nutritionalAnalysis;
  final String storageAdvice;
  final String reheatingInstructions;
  final String consumptionIdeas;
  final String imagePath;

  EnrichedFoodData({
    required this.name,
    required this.nutritionalAnalysis,
    required this.storageAdvice,
    required this.reheatingInstructions,
    required this.consumptionIdeas,
    required this.imagePath,
  });

  factory EnrichedFoodData.fromJson(Map<String, dynamic> json) {
    return EnrichedFoodData(
      name: json['name'] ?? '',
      nutritionalAnalysis: json['nutritional_analysis'] ?? '',
      storageAdvice: json['storage_advice'] ?? '',
      reheatingInstructions: json['reheating_instructions'] ?? '',
      consumptionIdeas: json['consumption_ideas'] ?? '',
      imagePath: json['image_path'] ?? '',
    );
  }
}
```

### **💻 Implementación Flutter**
```dart
class InventoryService {
  static const String baseUrl = 'http://your-api-url.com';
  
  Future<FoodsFromRecognitionResponse> addFoodsFromRecognition({
    required List<FoodRecognitionData> foods,
    required String jwtToken,
  }) async {
    try {
      final request = FoodsFromRecognitionRequest(foods: foods);
      
      final response = await http.post(
        Uri.parse('$baseUrl/api/inventory/foods/from-recognition'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $jwtToken',
        },
        body: jsonEncode(request.toJson()),
      );

      if (response.statusCode == 200) {
        final responseData = jsonDecode(response.body);
        return FoodsFromRecognitionResponse.fromJson(responseData);
      } else if (response.statusCode == 401) {
        throw Exception('Token de autenticación inválido o expirado');
      } else {
        throw Exception('Error del servidor: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error de conexión: $e');
    }
  }
}
```

---

## 📚 **2. ENDPOINT: RECETAS POR DEFECTO**

### **📋 Información Técnica**
```dart
// URL del endpoint
static const String DEFAULT_RECIPES_URL = '/api/recipes/default';

// Método HTTP
static const String METHOD = 'GET';

// Headers (NO requiere autenticación)
Map<String, String> headers = {
  'Content-Type': 'application/json',
  // ✅ NO REQUIERE Authorization header
};
```

### **📦 Estructura de Response**
```dart
class DefaultRecipesResponse {
  final int totalRecipes;
  final String filterApplied;
  final Map<String, int> categoriesSummary;
  final List<DefaultRecipe> defaultRecipes;

  DefaultRecipesResponse({
    required this.totalRecipes,
    required this.filterApplied,
    required this.categoriesSummary,
    required this.defaultRecipes,
  });

  factory DefaultRecipesResponse.fromJson(Map<String, dynamic> json) {
    return DefaultRecipesResponse(
      totalRecipes: json['total_recipes'] ?? 0,
      filterApplied: json['filter_applied'] ?? 'none',
      categoriesSummary: Map<String, int>.from(json['categories_summary'] ?? {}),
      defaultRecipes: (json['default_recipes'] as List<dynamic>?)
          ?.map((item) => DefaultRecipe.fromJson(item))
          .toList() ?? [],
    );
  }
}

class DefaultRecipe {
  final String uid;
  final String title;
  final String duration;
  final String difficulty;
  final String category;
  final String description;
  final String footer;
  final String? imagePath;
  final String imageStatus;
  final List<RecipeIngredient> ingredients;
  final List<RecipeStep> steps;

  DefaultRecipe({
    required this.uid,
    required this.title,
    required this.duration,
    required this.difficulty,
    required this.category,
    required this.description,
    required this.footer,
    this.imagePath,
    required this.imageStatus,
    required this.ingredients,
    required this.steps,
  });

  factory DefaultRecipe.fromJson(Map<String, dynamic> json) {
    return DefaultRecipe(
      uid: json['uid'] ?? '',
      title: json['title'] ?? '',
      duration: json['duration'] ?? '',
      difficulty: json['difficulty'] ?? '',
      category: json['category'] ?? '',
      description: json['description'] ?? '',
      footer: json['footer'] ?? '',
      imagePath: json['image_path'],
      imageStatus: json['image_status'] ?? 'pending',
      ingredients: (json['ingredients'] as List<dynamic>?)
          ?.map((item) => RecipeIngredient.fromJson(item))
          .toList() ?? [],
      steps: (json['steps'] as List<dynamic>?)
          ?.map((item) => RecipeStep.fromJson(item))
          .toList() ?? [],
    );
  }
}

class RecipeIngredient {
  final String name;
  final double quantity;
  final String typeUnit;

  RecipeIngredient({
    required this.name,
    required this.quantity,
    required this.typeUnit,
  });

  factory RecipeIngredient.fromJson(Map<String, dynamic> json) {
    return RecipeIngredient(
      name: json['name'] ?? '',
      quantity: (json['quantity'] ?? 0).toDouble(),
      typeUnit: json['type_unit'] ?? '',
    );
  }
}

class RecipeStep {
  final int stepOrder;
  final String description;

  RecipeStep({
    required this.stepOrder,
    required this.description,
  });

  factory RecipeStep.fromJson(Map<String, dynamic> json) {
    return RecipeStep(
      stepOrder: json['step_order'] ?? 0,
      description: json['description'] ?? '',
    );
  }
}
```

### **💻 Implementación Flutter**
```dart
class RecipesService {
  static const String baseUrl = 'http://your-api-url.com';
  
  Future<DefaultRecipesResponse> getDefaultRecipes({
    String? category, // Filtro opcional por categoría
  }) async {
    try {
      String url = '$baseUrl/api/recipes/default';
      
      // Agregar filtro de categoría si se especifica
      if (category != null && category.isNotEmpty) {
        url += '?category=$category';
      }
      
      final response = await http.get(
        Uri.parse(url),
        headers: {
          'Content-Type': 'application/json',
          // NO requiere Authorization
        },
      );

      if (response.statusCode == 200) {
        final responseData = jsonDecode(response.body);
        return DefaultRecipesResponse.fromJson(responseData);
      } else {
        throw Exception('Error del servidor: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error de conexión: $e');
    }
  }
}
```

---

## 📊 **RESUMEN TÉCNICO PARA DESARROLLO**

### **✅ Endpoints Listos para Integrar:**

1. **🍽️ POST /api/inventory/foods/from-recognition**
   - ✅ Funcional y probado
   - ✅ Requiere JWT token
   - ✅ Enriquece datos con IA
   - ✅ Procesa múltiples comidas
   - ✅ Manejo de errores completo

2. **📚 GET /api/recipes/default**
   - ✅ Funcional y probado
   - ✅ 15 recetas con imágenes de alta calidad
   - ✅ Filtrado por categorías
   - ✅ NO requiere autenticación
   - ✅ Ingredientes y pasos detallados

### **🚀 Beneficios para la App:**

- **🎨 Imágenes de Alta Calidad**: Todas las recetas incluyen imágenes generadas con IA
- **📱 UX Mejorada**: Flujo completo desde reconocimiento hasta inventario
- **⚡ Performance**: Endpoints optimizados y rápidos
- **🔒 Seguridad**: Autenticación JWT donde es necesaria
- **📊 Datos Ricos**: Información nutricional y consejos de conservación

### **🛠️ Próximos Pasos:**

1. **Implementar las clases Dart** proporcionadas
2. **Integrar con el flujo de reconocimiento** existente
3. **Crear las pantallas de UI** con los widgets proporcionados
4. **Probar la integración** con tokens JWT reales
5. **Optimizar imágenes** para diferentes tamaños de pantalla

---

## 📞 **Soporte Técnico**

Si necesitas ayuda con la integración, estos endpoints están completamente funcionales y documentados. Todas las recetas incluyen imágenes de alta calidad generadas automáticamente y datos enriquecidos para una experiencia de usuario superior.

¡La API está lista para potenciar tu app Flutter! 🚀 