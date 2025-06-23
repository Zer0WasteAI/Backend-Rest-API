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

### **🎯 Ejemplo de Uso**
```dart
// Ejemplo de uso después del reconocimiento de imágenes
Future<void> addRecognizedFoodsToInventory() async {
  try {
    // Datos que vienen del reconocimiento
    final recognizedFoods = [
      FoodRecognitionData(
        name: 'Lasaña de verduras',
        description: 'Lasaña casera con capas de pasta, espinacas, ricotta y salsa de tomate',
        mainIngredients: ['pasta', 'espinacas', 'ricotta', 'salsa de tomate'],
        category: 'almuerzo',
        storageType: 'refrigerador',
        expirationTime: 3,
        timeUnit: 'days',
        tips: 'Recalentar en horno a 180°C por 15 minutos',
        servingQuantity: 4,
        calories: 320,
        imagePath: 'https://storage.googleapis.com/bucket/lasagna.jpg',
      ),
    ];

    final response = await InventoryService().addFoodsFromRecognition(
      foods: recognizedFoods,
      jwtToken: await getJwtToken(),
    );

    if (response.success) {
      // Mostrar éxito
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('${response.successfullyAdded} comidas agregadas al inventario'),
          backgroundColor: Colors.green,
        ),
      );
      
      // Navegar a inventario o actualizar UI
      Navigator.pushNamed(context, '/inventory');
    } else {
      // Mostrar errores
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: Text('Error'),
          content: Text(response.message),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text('OK'),
            ),
          ],
        ),
      );
    }
  } catch (e) {
    // Manejo de errores
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Error: $e'),
        backgroundColor: Colors.red,
      ),
    );
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

### **🎨 Widget de Recetas (UI Completa)**
```dart
class DefaultRecipesScreen extends StatefulWidget {
  @override
  _DefaultRecipesScreenState createState() => _DefaultRecipesScreenState();
}

class _DefaultRecipesScreenState extends State<DefaultRecipesScreen> {
  final RecipesService _recipesService = RecipesService();
  DefaultRecipesResponse? _recipesResponse;
  bool _isLoading = true;
  String? _selectedCategory;

  final List<String> _categories = [
    'destacadas',
    'rapidas_faciles', 
    'vegetarianas',
    'postres',
    'saludables'
  ];

  final Map<String, String> _categoryLabels = {
    'destacadas': '🌟 Destacadas',
    'rapidas_faciles': '⚡ Rápidas y Fáciles',
    'vegetarianas': '🥬 Vegetarianas',
    'postres': '🍰 Postres',
    'saludables': '💚 Saludables',
  };

  @override
  void initState() {
    super.initState();
    _loadRecipes();
  }

  Future<void> _loadRecipes([String? category]) async {
    setState(() {
      _isLoading = true;
      _selectedCategory = category;
    });

    try {
      final response = await _recipesService.getDefaultRecipes(
        category: category,
      );
      
      setState(() {
        _recipesResponse = response;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error cargando recetas: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Recetas ZeroWaste'),
        backgroundColor: Colors.green[600],
        elevation: 0,
      ),
      body: Column(
        children: [
          // Filtros de categoría
          Container(
            height: 60,
            padding: EdgeInsets.symmetric(vertical: 8),
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: EdgeInsets.symmetric(horizontal: 16),
              children: [
                _buildCategoryChip('Todas', null),
                SizedBox(width: 8),
                ..._categories.map((category) => Padding(
                  padding: EdgeInsets.only(right: 8),
                  child: _buildCategoryChip(
                    _categoryLabels[category] ?? category,
                    category,
                  ),
                )),
              ],
            ),
          ),
          
          // Contenido principal
          Expanded(
            child: _isLoading
                ? Center(child: CircularProgressIndicator())
                : _recipesResponse == null
                    ? Center(child: Text('No se pudieron cargar las recetas'))
                    : _buildRecipesList(),
          ),
        ],
      ),
    );
  }

  Widget _buildCategoryChip(String label, String? category) {
    final bool isSelected = _selectedCategory == category;
    
    return FilterChip(
      label: Text(label),
      selected: isSelected,
      onSelected: (selected) {
        _loadRecipes(selected ? category : null);
      },
      selectedColor: Colors.green[100],
      checkmarkColor: Colors.green[800],
    );
  }

  Widget _buildRecipesList() {
    final recipes = _recipesResponse!.defaultRecipes;
    
    if (recipes.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.restaurant, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text('No hay recetas disponibles'),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: EdgeInsets.all(16),
      itemCount: recipes.length,
      itemBuilder: (context, index) {
        final recipe = recipes[index];
        return _buildRecipeCard(recipe);
      },
    );
  }

  Widget _buildRecipeCard(DefaultRecipe recipe) {
    return Card(
      margin: EdgeInsets.only(bottom: 16),
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: InkWell(
        onTap: () => _openRecipeDetail(recipe),
        borderRadius: BorderRadius.circular(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Imagen de la receta
            ClipRRect(
              borderRadius: BorderRadius.vertical(top: Radius.circular(12)),
              child: AspectRatio(
                aspectRatio: 16 / 9,
                child: recipe.imagePath != null
                    ? Image.network(
                        recipe.imagePath!,
                        fit: BoxFit.cover,
                        errorBuilder: (context, error, stackTrace) {
                          return Container(
                            color: Colors.grey[200],
                            child: Icon(Icons.image_not_supported, size: 64),
                          );
                        },
                      )
                    : Container(
                        color: Colors.grey[200],
                        child: Icon(Icons.restaurant, size: 64),
                      ),
              ),
            ),
            
            // Contenido de la tarjeta
            Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Título y dificultad
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Text(
                          recipe.title,
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      Container(
                        padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: _getDifficultyColor(recipe.difficulty),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          recipe.difficulty,
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ),
                  
                  SizedBox(height: 8),
                  
                  // Descripción
                  Text(
                    recipe.description,
                    style: TextStyle(
                      color: Colors.grey[600],
                      fontSize: 14,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  
                  SizedBox(height: 12),
                  
                  // Información adicional
                  Row(
                    children: [
                      Icon(Icons.timer, size: 16, color: Colors.grey[600]),
                      SizedBox(width: 4),
                      Text(
                        recipe.duration,
                        style: TextStyle(color: Colors.grey[600], fontSize: 12),
                      ),
                      SizedBox(width: 16),
                      Icon(Icons.restaurant_menu, size: 16, color: Colors.grey[600]),
                      SizedBox(width: 4),
                      Text(
                        '${recipe.ingredients.length} ingredientes',
                        style: TextStyle(color: Colors.grey[600], fontSize: 12),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _getDifficultyColor(String difficulty) {
    switch (difficulty.toLowerCase()) {
      case 'fácil':
        return Colors.green;
      case 'intermedio':
        return Colors.orange;
      case 'difícil':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  void _openRecipeDetail(DefaultRecipe recipe) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => RecipeDetailScreen(recipe: recipe),
      ),
    );
  }
}
```

### **🎯 Pantalla de Detalle de Receta**
```dart
class RecipeDetailScreen extends StatelessWidget {
  final DefaultRecipe recipe;

  const RecipeDetailScreen({Key? key, required this.recipe}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: CustomScrollView(
        slivers: [
          // App Bar con imagen
          SliverAppBar(
            expandedHeight: 250,
            pinned: true,
            flexibleSpace: FlexibleSpaceBar(
              title: Text(
                recipe.title,
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  shadows: [Shadow(color: Colors.black54, blurRadius: 2)],
                ),
              ),
              background: recipe.imagePath != null
                  ? Image.network(
                      recipe.imagePath!,
                      fit: BoxFit.cover,
                    )
                  : Container(
                      color: Colors.grey[300],
                      child: Icon(Icons.restaurant, size: 64),
                    ),
            ),
          ),
          
          // Contenido
          SliverToBoxAdapter(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Información básica
                  Row(
                    children: [
                      _buildInfoChip(Icons.timer, recipe.duration),
                      SizedBox(width: 12),
                      _buildInfoChip(Icons.signal_cellular_alt, recipe.difficulty),
                      SizedBox(width: 12),
                      _buildInfoChip(Icons.restaurant_menu, '${recipe.ingredients.length} ingredientes'),
                    ],
                  ),
                  
                  SizedBox(height: 16),
                  
                  // Descripción
                  Text(
                    recipe.description,
                    style: TextStyle(fontSize: 16, height: 1.5),
                  ),
                  
                  SizedBox(height: 24),
                  
                  // Ingredientes
                  Text(
                    'Ingredientes',
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                  
                  SizedBox(height: 12),
                  
                  ...recipe.ingredients.map((ingredient) => Padding(
                    padding: EdgeInsets.only(bottom: 8),
                    child: Row(
                      children: [
                        Container(
                          width: 6,
                          height: 6,
                          decoration: BoxDecoration(
                            color: Colors.green,
                            shape: BoxShape.circle,
                          ),
                        ),
                        SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            '${ingredient.quantity} ${ingredient.typeUnit} de ${ingredient.name}',
                            style: TextStyle(fontSize: 16),
                          ),
                        ),
                      ],
                    ),
                  )),
                  
                  SizedBox(height: 24),
                  
                  // Preparación
                  Text(
                    'Preparación',
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                  
                  SizedBox(height: 12),
                  
                  ...recipe.steps.map((step) => Padding(
                    padding: EdgeInsets.only(bottom: 16),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          width: 24,
                          height: 24,
                          decoration: BoxDecoration(
                            color: Colors.green,
                            shape: BoxShape.circle,
                          ),
                          child: Center(
                            child: Text(
                              '${step.stepOrder}',
                              style: TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                                fontSize: 12,
                              ),
                            ),
                          ),
                        ),
                        SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            step.description,
                            style: TextStyle(fontSize: 16, height: 1.5),
                          ),
                        ),
                      ],
                    ),
                  )),
                  
                  SizedBox(height: 24),
                  
                  // Footer
                  Container(
                    width: double.infinity,
                    padding: EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.green[50],
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.green[200]!),
                    ),
                    child: Text(
                      recipe.footer,
                      style: TextStyle(
                        fontSize: 14,
                        fontStyle: FontStyle.italic,
                        color: Colors.green[800],
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoChip(IconData icon, String label) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.grey[100],
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: Colors.grey[600]),
          SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(fontSize: 12, color: Colors.grey[600]),
          ),
        ],
      ),
    );
  }
}
```

### **🎯 Ejemplo de Uso Completo**
```dart
// En tu main.dart o donde manejes las rutas
void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ZeroWaste AI',
      theme: ThemeData(
        primarySwatch: Colors.green,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      routes: {
        '/': (context) => HomeScreen(),
        '/recipes': (context) => DefaultRecipesScreen(),
        '/inventory': (context) => InventoryScreen(),
      },
    );
  }
}

// Uso en tu HomeScreen o donde sea necesario
class HomeScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('ZeroWaste AI')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            ElevatedButton(
              onPressed: () {
                Navigator.pushNamed(context, '/recipes');
              },
              child: Text('Ver Recetas por Defecto'),
            ),
            SizedBox(height: 16),
            ElevatedButton(
              onPressed: () {
                // Aquí implementarías el flujo de reconocimiento
                // y luego llamarías a addFoodsFromRecognition
              },
              child: Text('Reconocer y Agregar Comidas'),
            ),
          ],
        ),
      ),
    );
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