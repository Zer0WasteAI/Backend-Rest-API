#!/usr/bin/env python3
"""
Script para generar 15 recetas por defecto disponibles para todos los usuarios.
Estas recetas estarán organizadas por categorías y serán accesibles desde la app.
"""

import sys
import os
import uuid
from datetime import datetime, timezone

# Agregar el directorio src al path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.infrastructure.db.base import db
from src.infrastructure.db.models.recipe_orm import RecipeORM
from src.infrastructure.db.models.recipe_ingredient_orm import RecipeIngredientORM
from src.infrastructure.db.models.recipe_step_orm import RecipeStepORM
from src.infrastructure.db.schemas.user_schema import User
from src.application.factories.recipe_usecase_factory import make_recipe_image_generator_service
from src.main import create_app

# UID especial para recetas del sistema (disponibles para todos)
SYSTEM_USER_UID = "SYSTEM_DEFAULT_RECIPES"

# Definición de las 15 recetas por defecto organizadas por categorías
# Cada receta incluye ingredientes detallados, pasos específicos y se generará imagen automáticamente
RECIPES_DATA = {
    "destacadas": [
        {
            "title": "Pasta Carbonara Clásica",
            "duration": "30 minutos",
            "difficulty": "Intermedio",
            "category": "almuerzo",
            "description": "La auténtica receta italiana de carbonara con huevos, bacon y queso parmesano. Cremosa y deliciosa.",
            "ingredients": [
                {"name": "Pasta (espaguetis)", "quantity": 400, "type_unit": "gr"},
                {"name": "Huevos", "quantity": 4, "type_unit": "unidades"},
                {"name": "Bacon o panceta", "quantity": 200, "type_unit": "gr"},
                {"name": "Queso parmesano rallado", "quantity": 100, "type_unit": "gr"},
                {"name": "Pimienta negra", "quantity": 1, "type_unit": "cucharadita"},
                {"name": "Sal", "quantity": 1, "type_unit": "pizca"}
            ],
            "steps": [
                {"step_order": 1, "description": "Cocinar la pasta en agua con sal hasta que esté al dente"},
                {"step_order": 2, "description": "Freír el bacon hasta que esté crujiente y reservar"},
                {"step_order": 3, "description": "Batir los huevos con el queso parmesano y pimienta"},
                {"step_order": 4, "description": "Mezclar la pasta caliente con los huevos, removiendo rápidamente"},
                {"step_order": 5, "description": "Agregar el bacon y servir inmediatamente"}
            ],
            "footer": "Un clásico italiano que nunca falla"
        },
        {
            "title": "Pollo Teriyaki Glaseado con Arroz Jazmín",
            "duration": "35 minutos",
            "difficulty": "Fácil",
            "category": "cena",
            "description": "Pollo jugoso bañado en salsa teriyaki casera con el equilibrio perfecto entre dulce y salado. Acompañado de arroz jazmín aromático y vegetales salteados. Una fusión japonesa que conquista paladares.",
            "ingredients": [
                {"name": "Muslos de pollo deshuesados", "quantity": 600, "type_unit": "gr"},
                {"name": "Arroz jazmín", "quantity": 300, "type_unit": "gr"},
                {"name": "Salsa de soja baja en sodio", "quantity": 80, "type_unit": "ml"},
                {"name": "Miel de abeja", "quantity": 45, "type_unit": "ml"},
                {"name": "Sake o vino blanco", "quantity": 30, "type_unit": "ml"},
                {"name": "Mirin", "quantity": 30, "type_unit": "ml"},
                {"name": "Ajo fresco", "quantity": 3, "type_unit": "dientes"},
                {"name": "Jengibre fresco", "quantity": 20, "type_unit": "gr"},
                {"name": "Aceite de sésamo", "quantity": 15, "type_unit": "ml"},
                {"name": "Aceite vegetal", "quantity": 30, "type_unit": "ml"},
                {"name": "Semillas de sésamo", "quantity": 15, "type_unit": "gr"},
                {"name": "Cebollín fresco", "quantity": 3, "type_unit": "tallos"},
                {"name": "Brócoli", "quantity": 200, "type_unit": "gr"}
            ],
            "steps": [
                {"step_order": 1, "description": "Lavar el arroz hasta que el agua salga clara. Cocinarlo con 1.5 veces su volumen de agua por 18 minutos."},
                {"step_order": 2, "description": "Cortar el pollo en trozos de 3cm. Salpimentar y dejar reposar 10 minutos a temperatura ambiente."},
                {"step_order": 3, "description": "Preparar la salsa teriyaki: mezclar soja, miel, sake, mirin, ajo y jengibre rallados. Reservar."},
                {"step_order": 4, "description": "Calentar aceite vegetal en wok o sartén grande a fuego alto. Sellar el pollo hasta dorar por todos lados (5-6 min)."},
                {"step_order": 5, "description": "Reducir fuego a medio, agregar la salsa teriyaki y cocinar 8-10 minutos hasta que el pollo esté cocido."},
                {"step_order": 6, "description": "En los últimos 3 minutos, añadir brócoli cortado en floretes pequeños para que se cocine al vapor."},
                {"step_order": 7, "description": "Cuando la salsa esté espesa y brillante, rociar con aceite de sésamo y mezclar."},
                {"step_order": 8, "description": "Servir sobre arroz caliente, espolvorear con sésamo y cebollín picado. ¡Itadakimasu!"}
            ],
            "footer": "El balance perfecto entre tradición japonesa y sabor casero"
        },
        {
            "title": "Ensalada César con Pollo",
            "duration": "20 minutos",
            "difficulty": "Fácil",
            "category": "ensalada",
            "description": "Clásica ensalada César con pollo grillado, crutones caseros y aderezo cremoso. Fresca y nutritiva.",
            "ingredients": [
                {"name": "Lechuga romana", "quantity": 2, "type_unit": "cabezas"},
                {"name": "Pechuga de pollo", "quantity": 300, "type_unit": "gr"},
                {"name": "Pan de molde", "quantity": 4, "type_unit": "rebanadas"},
                {"name": "Queso parmesano", "quantity": 50, "type_unit": "gr"},
                {"name": "Mayonesa", "quantity": 80, "type_unit": "ml"},
                {"name": "Limón", "quantity": 1, "type_unit": "unidad"},
                {"name": "Anchoas", "quantity": 3, "type_unit": "filetes"}
            ],
            "steps": [
                {"step_order": 1, "description": "Grillar el pollo sazonado hasta cocinar completamente"},
                {"step_order": 2, "description": "Cortar el pan en cubos y tostar hasta dorar"},
                {"step_order": 3, "description": "Lavar y cortar la lechuga en trozos"},
                {"step_order": 4, "description": "Preparar aderezo con mayonesa, limón y anchoas"},
                {"step_order": 5, "description": "Mezclar lechuga con aderezo y crutones"},
                {"step_order": 6, "description": "Coronar con pollo cortado y queso parmesano"}
            ],
            "footer": "Un clásico que siempre satisface"
        }
    ],
    "rapidas_faciles": [
        {
            "title": "Quesadillas de Queso y Jamón",
            "duration": "10 minutos",
            "difficulty": "Fácil",
            "category": "almuerzo",
            "description": "Quesadillas crujientes rellenas de queso derretido y jamón. Perfectas para una comida rápida.",
            "ingredients": [
                {"name": "Tortillas de trigo", "quantity": 4, "type_unit": "unidades"},
                {"name": "Queso rallado", "quantity": 200, "type_unit": "gr"},
                {"name": "Jamón cocido", "quantity": 150, "type_unit": "gr"},
                {"name": "Cebolla", "quantity": 1, "type_unit": "unidad"},
                {"name": "Aceite", "quantity": 15, "type_unit": "ml"}
            ],
            "steps": [
                {"step_order": 1, "description": "Picar la cebolla finamente"},
                {"step_order": 2, "description": "Rellenar las tortillas con queso, jamón y cebolla"},
                {"step_order": 3, "description": "Doblar las tortillas por la mitad"},
                {"step_order": 4, "description": "Cocinar en sartén con aceite hasta dorar"},
                {"step_order": 5, "description": "Servir calientes cortadas en triángulos"}
            ],
            "footer": "Rápidas, fáciles y deliciosas"
        },
        {
            "title": "Huevos Revueltos con Tostadas",
            "duration": "8 minutos",
            "difficulty": "Fácil",
            "category": "desayuno",
            "description": "Desayuno clásico con huevos cremosos y tostadas doradas. El inicio perfecto para el día.",
            "ingredients": [
                {"name": "Huevos", "quantity": 4, "type_unit": "unidades"},
                {"name": "Pan de molde", "quantity": 4, "type_unit": "rebanadas"},
                {"name": "Mantequilla", "quantity": 30, "type_unit": "gr"},
                {"name": "Leche", "quantity": 60, "type_unit": "ml"},
                {"name": "Sal", "quantity": 1, "type_unit": "pizca"},
                {"name": "Pimienta", "quantity": 1, "type_unit": "pizca"}
            ],
            "steps": [
                {"step_order": 1, "description": "Tostar el pan hasta dorarlo"},
                {"step_order": 2, "description": "Batir los huevos con leche, sal y pimienta"},
                {"step_order": 3, "description": "Derretir mantequilla en sartén a fuego medio"},
                {"step_order": 4, "description": "Agregar huevos y revolver suavemente hasta cuajar"},
                {"step_order": 5, "description": "Servir inmediatamente sobre las tostadas"}
            ],
            "footer": "El desayuno de siempre, siempre delicioso"
        },
        {
            "title": "Sándwich de Atún",
            "duration": "5 minutos",
            "difficulty": "Fácil",
            "category": "almuerzo",
            "description": "Sándwich nutritivo de atún con vegetales frescos. Ideal para llevar o comer en casa.",
            "ingredients": [
                {"name": "Pan de molde", "quantity": 4, "type_unit": "rebanadas"},
                {"name": "Atún en lata", "quantity": 2, "type_unit": "latas"},
                {"name": "Mayonesa", "quantity": 40, "type_unit": "ml"},
                {"name": "Tomate", "quantity": 1, "type_unit": "unidad"},
                {"name": "Lechuga", "quantity": 4, "type_unit": "hojas"},
                {"name": "Cebolla", "quantity": 0.5, "type_unit": "unidad"}
            ],
            "steps": [
                {"step_order": 1, "description": "Escurrir el atún y desmenuzarlo"},
                {"step_order": 2, "description": "Mezclar atún con mayonesa y cebolla picada"},
                {"step_order": 3, "description": "Cortar el tomate en rodajas"},
                {"step_order": 4, "description": "Armar sándwich con lechuga, atún y tomate"},
                {"step_order": 5, "description": "Cortar diagonalmente y servir"}
            ],
            "footer": "Práctico y nutritivo para cualquier momento"
        }
    ],
    "vegetarianas": [
        {
            "title": "Curry de Lentejas",
            "duration": "35 minutos",
            "difficulty": "Intermedio",
            "category": "cena",
            "description": "Curry aromático de lentejas con especias tradicionales. Rico en proteínas y sabor.",
            "ingredients": [
                {"name": "Lentejas rojas", "quantity": 250, "type_unit": "gr"},
                {"name": "Leche de coco", "quantity": 400, "type_unit": "ml"},
                {"name": "Cebolla", "quantity": 1, "type_unit": "unidad"},
                {"name": "Ajo", "quantity": 3, "type_unit": "dientes"},
                {"name": "Jengibre", "quantity": 15, "type_unit": "gr"},
                {"name": "Curry en polvo", "quantity": 15, "type_unit": "gr"},
                {"name": "Tomate", "quantity": 2, "type_unit": "unidades"}
            ],
            "steps": [
                {"step_order": 1, "description": "Lavar las lentejas hasta que el agua salga clara"},
                {"step_order": 2, "description": "Picar cebolla, ajo y jengibre finamente"},
                {"step_order": 3, "description": "Sofreír la cebolla hasta transparentar"},
                {"step_order": 4, "description": "Agregar ajo, jengibre y curry, cocinar 1 minuto"},
                {"step_order": 5, "description": "Añadir tomate picado y lentejas"},
                {"step_order": 6, "description": "Verter leche de coco y cocinar 25 minutos"},
                {"step_order": 7, "description": "Sazonar y servir con arroz"}
            ],
            "footer": "Nutritivo y reconfortante plato vegetariano"
        },
        {
            "title": "Ensalada Mediterránea",
            "duration": "15 minutos",
            "difficulty": "Fácil",
            "category": "ensalada",
            "description": "Ensalada fresca con ingredientes mediterráneos. Saludable y llena de sabor.",
            "ingredients": [
                {"name": "Tomates cherry", "quantity": 300, "type_unit": "gr"},
                {"name": "Pepino", "quantity": 2, "type_unit": "unidades"},
                {"name": "Queso feta", "quantity": 150, "type_unit": "gr"},
                {"name": "Aceitunas negras", "quantity": 100, "type_unit": "gr"},
                {"name": "Cebolla morada", "quantity": 0.5, "type_unit": "unidad"},
                {"name": "Aceite de oliva", "quantity": 60, "type_unit": "ml"},
                {"name": "Limón", "quantity": 1, "type_unit": "unidad"}
            ],
            "steps": [
                {"step_order": 1, "description": "Cortar tomates cherry por la mitad"},
                {"step_order": 2, "description": "Cortar pepino en rodajas"},
                {"step_order": 3, "description": "Cortar cebolla en juliana fina"},
                {"step_order": 4, "description": "Desmenuzar el queso feta"},
                {"step_order": 5, "description": "Mezclar todos los ingredientes"},
                {"step_order": 6, "description": "Aliñar con aceite de oliva y jugo de limón"}
            ],
            "footer": "Fresca y saludable como el Mediterráneo"
        },
        {
            "title": "Pasta Primavera",
            "duration": "20 minutos",
            "difficulty": "Fácil",
            "category": "almuerzo",
            "description": "Pasta con vegetales frescos de temporada en salsa ligera. Colorida y nutritiva.",
            "ingredients": [
                {"name": "Pasta (penne)", "quantity": 350, "type_unit": "gr"},
                {"name": "Calabacín", "quantity": 1, "type_unit": "unidad"},
                {"name": "Pimiento rojo", "quantity": 1, "type_unit": "unidad"},
                {"name": "Brócoli", "quantity": 200, "type_unit": "gr"},
                {"name": "Ajo", "quantity": 2, "type_unit": "dientes"},
                {"name": "Aceite de oliva", "quantity": 45, "type_unit": "ml"},
                {"name": "Queso parmesano", "quantity": 80, "type_unit": "gr"}
            ],
            "steps": [
                {"step_order": 1, "description": "Cocinar la pasta según instrucciones del paquete"},
                {"step_order": 2, "description": "Cortar todos los vegetales en trozos uniformes"},
                {"step_order": 3, "description": "Saltear ajo en aceite de oliva"},
                {"step_order": 4, "description": "Agregar vegetales y cocinar hasta tiernos"},
                {"step_order": 5, "description": "Mezclar pasta con vegetales"},
                {"step_order": 6, "description": "Servir con queso parmesano rallado"}
            ],
            "footer": "Los colores y sabores de la primavera"
        }
    ],
    "postres": [
        {
            "title": "Tiramisú Auténtico Italiano",
            "duration": "45 minutos + 6 horas refrigeración",
            "difficulty": "Intermedio",
            "category": "postre",
            "description": "El auténtico tiramisú de la región del Véneto, con la técnica tradicional italiana. Capas perfectas de savoiardi empapados en espresso, crema de mascarpone sedosa y un toque de amaretto. El postre que significa 'levántame el ánimo'.",
            "ingredients": [
                {"name": "Savoiardi (bizcochos de soletilla)", "quantity": 400, "type_unit": "gr"},
                {"name": "Café espresso fuerte", "quantity": 500, "type_unit": "ml"},
                {"name": "Queso mascarpone italiano", "quantity": 500, "type_unit": "gr"},
                {"name": "Yemas de huevo frescas", "quantity": 6, "type_unit": "unidades"},
                {"name": "Azúcar blanca refinada", "quantity": 150, "type_unit": "gr"},
                {"name": "Claras de huevo", "quantity": 3, "type_unit": "unidades"},
                {"name": "Cacao amargo en polvo", "quantity": 40, "type_unit": "gr"},
                {"name": "Amaretto di Saronno", "quantity": 60, "type_unit": "ml"},
                {"name": "Azúcar glass", "quantity": 30, "type_unit": "gr"},
                {"name": "Sal fina", "quantity": 1, "type_unit": "pizca"}
            ],
            "steps": [
                {"step_order": 1, "description": "Preparar espresso doble muy fuerte y mezclarlo con amaretto. Dejar enfriar completamente a temperatura ambiente."},
                {"step_order": 2, "description": "En un bowl grande, batir las yemas con 100g de azúcar hasta obtener una crema pálida y espumosa (5-7 minutos)."},
                {"step_order": 3, "description": "Incorporar el mascarpone a temperatura ambiente a las yemas, mezclando suavemente con movimientos envolventes."},
                {"step_order": 4, "description": "En otro bowl limpio, montar las claras con una pizca de sal hasta obtener picos blandos. Agregar 50g de azúcar y batir hasta picos firmes."},
                {"step_order": 5, "description": "Incorporar 1/3 de las claras a la mezcla de mascarpone con movimientos envolventes. Luego agregar el resto en dos tandas."},
                {"step_order": 6, "description": "Sumergir rápidamente cada savoiardi en el café (2-3 segundos por lado) y colocar en el fondo de una fuente rectangular."},
                {"step_order": 7, "description": "Cubrir con la mitad de la crema de mascarpone, alisando con espátula. Repetir con otra capa de bizcochos y crema."},
                {"step_order": 8, "description": "Cubrir con film transparente y refrigerar mínimo 6 horas, idealmente toda la noche."},
                {"step_order": 9, "description": "Antes de servir, tamizar generosamente el cacao amargo por toda la superficie. ¡Buon appetito!"}
            ],
            "footer": "Tirami-sù: el postre que levanta el ánimo desde 1960"
        },
        {
            "title": "Brownies de Chocolate",
            "duration": "45 minutos",
            "difficulty": "Fácil",
            "category": "postre",
            "description": "Brownies húmedos y chocolatosos. El antojo perfecto para los amantes del chocolate.",
            "ingredients": [
                {"name": "Chocolate negro", "quantity": 200, "type_unit": "gr"},
                {"name": "Mantequilla", "quantity": 150, "type_unit": "gr"},
                {"name": "Azúcar", "quantity": 200, "type_unit": "gr"},
                {"name": "Huevos", "quantity": 3, "type_unit": "unidades"},
                {"name": "Harina", "quantity": 100, "type_unit": "gr"},
                {"name": "Cacao en polvo", "quantity": 30, "type_unit": "gr"},
                {"name": "Nueces", "quantity": 100, "type_unit": "gr"}
            ],
            "steps": [
                {"step_order": 1, "description": "Precalentar horno a 180°C"},
                {"step_order": 2, "description": "Derretir chocolate con mantequilla"},
                {"step_order": 3, "description": "Batir huevos con azúcar hasta espumar"},
                {"step_order": 4, "description": "Incorporar chocolate derretido"},
                {"step_order": 5, "description": "Agregar harina, cacao y nueces"},
                {"step_order": 6, "description": "Verter en molde y hornear 25 minutos"}
            ],
            "footer": "Irresistibles y adictivos"
        },
        {
            "title": "Flan de Vainilla",
            "duration": "60 minutos + refrigeración",
            "difficulty": "Intermedio",
            "category": "postre",
            "description": "Flan cremoso con caramelo dorado. Un clásico postre casero que nunca pasa de moda.",
            "ingredients": [
                {"name": "Leche", "quantity": 500, "type_unit": "ml"},
                {"name": "Huevos", "quantity": 4, "type_unit": "unidades"},
                {"name": "Azúcar", "quantity": 150, "type_unit": "gr"},
                {"name": "Azúcar para caramelo", "quantity": 100, "type_unit": "gr"},
                {"name": "Esencia de vainilla", "quantity": 5, "type_unit": "ml"}
            ],
            "steps": [
                {"step_order": 1, "description": "Hacer caramelo con 100gr de azúcar"},
                {"step_order": 2, "description": "Cubrir el fondo del molde con caramelo"},
                {"step_order": 3, "description": "Calentar la leche con vainilla"},
                {"step_order": 4, "description": "Batir huevos con azúcar restante"},
                {"step_order": 5, "description": "Incorporar leche tibia a los huevos"},
                {"step_order": 6, "description": "Verter sobre caramelo y cocinar a baño maría 45 min"},
                {"step_order": 7, "description": "Enfriar y desmoldar"}
            ],
            "footer": "Suave, cremoso y con el caramelo perfecto"
        }
    ],
    "saludables": [
        {
            "title": "Bowl de Quinoa y Vegetales",
            "duration": "25 minutos",
            "difficulty": "Fácil",
            "category": "almuerzo",
            "description": "Bowl nutritivo con quinoa, vegetales asados y aderezo de tahini. Completo y saludable.",
            "ingredients": [
                {"name": "Quinoa", "quantity": 200, "type_unit": "gr"},
                {"name": "Brócoli", "quantity": 300, "type_unit": "gr"},
                {"name": "Zanahoria", "quantity": 2, "type_unit": "unidades"},
                {"name": "Palta", "quantity": 1, "type_unit": "unidad"},
                {"name": "Tahini", "quantity": 30, "type_unit": "ml"},
                {"name": "Limón", "quantity": 1, "type_unit": "unidad"},
                {"name": "Aceite de oliva", "quantity": 30, "type_unit": "ml"}
            ],
            "steps": [
                {"step_order": 1, "description": "Cocinar quinoa según instrucciones del paquete"},
                {"step_order": 2, "description": "Cortar vegetales y asar en horno 20 minutos"},
                {"step_order": 3, "description": "Preparar aderezo con tahini y limón"},
                {"step_order": 4, "description": "Cortar palta en láminas"},
                {"step_order": 5, "description": "Armar bowl con quinoa, vegetales y palta"},
                {"step_order": 6, "description": "Rociar con aderezo antes de servir"}
            ],
            "footer": "Nutritivo y energizante"
        },
        {
            "title": "Salmón a la Plancha con Espárragos",
            "duration": "20 minutos",
            "difficulty": "Fácil",
            "category": "cena",
            "description": "Salmón jugoso con espárragos salteados. Alto en omega-3 y muy saludable.",
            "ingredients": [
                {"name": "Filete de salmón", "quantity": 4, "type_unit": "unidades"},
                {"name": "Espárragos", "quantity": 500, "type_unit": "gr"},
                {"name": "Limón", "quantity": 2, "type_unit": "unidades"},
                {"name": "Aceite de oliva", "quantity": 30, "type_unit": "ml"},
                {"name": "Ajo", "quantity": 2, "type_unit": "dientes"},
                {"name": "Sal", "quantity": 1, "type_unit": "pizca"},
                {"name": "Pimienta", "quantity": 1, "type_unit": "pizca"}
            ],
            "steps": [
                {"step_order": 1, "description": "Sazonar salmón con sal, pimienta y limón"},
                {"step_order": 2, "description": "Limpiar y cortar extremos de espárragos"},
                {"step_order": 3, "description": "Cocinar salmón a la plancha 4 min por lado"},
                {"step_order": 4, "description": "Saltear espárragos con ajo en aceite"},
                {"step_order": 5, "description": "Servir salmón con espárragos y limón"}
            ],
            "footer": "Saludable y delicioso"
        },
        {
            "title": "Smoothie Verde Energizante",
            "duration": "5 minutos",
            "difficulty": "Fácil",
            "category": "desayuno",
            "description": "Smoothie nutritivo con espinacas, frutas y semillas. Perfecto para empezar el día con energía.",
            "ingredients": [
                {"name": "Espinacas frescas", "quantity": 100, "type_unit": "gr"},
                {"name": "Plátano", "quantity": 1, "type_unit": "unidad"},
                {"name": "Manzana verde", "quantity": 1, "type_unit": "unidad"},
                {"name": "Leche de almendras", "quantity": 250, "type_unit": "ml"},
                {"name": "Semillas de chía", "quantity": 15, "type_unit": "gr"},
                {"name": "Miel", "quantity": 15, "type_unit": "ml"},
                {"name": "Jugo de limón", "quantity": 10, "type_unit": "ml"}
            ],
            "steps": [
                {"step_order": 1, "description": "Lavar bien las espinacas y la manzana"},
                {"step_order": 2, "description": "Pelar el plátano y cortar la manzana"},
                {"step_order": 3, "description": "Colocar todos los ingredientes en la licuadora"},
                {"step_order": 4, "description": "Licuar hasta obtener consistencia cremosa"},
                {"step_order": 5, "description": "Servir inmediatamente en vaso alto"}
            ],
            "footer": "Verde, nutritivo y delicioso"
        }
    ]
}

def create_default_recipes():
    """Crea las 15 recetas por defecto en la base de datos"""
    
    print("🍳 Iniciando generación de recetas por defecto...")
    
    # Crear usuario del sistema si no existe
    print("👤 Verificando usuario del sistema...")
    system_user = User.query.filter_by(uid=SYSTEM_USER_UID).first()
    if not system_user:
        print("👤 Creando usuario del sistema...")
        system_user = User(
            uid=SYSTEM_USER_UID,
            email="system@zerowasteai.com",
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(system_user)
        db.session.commit()
        print("✅ Usuario del sistema creado")
    else:
        print("✅ Usuario del sistema ya existe")
    
    # Verificar si ya existen recetas del sistema
    existing_recipes = RecipeORM.query.filter_by(user_uid=SYSTEM_USER_UID).count()
    if existing_recipes > 0:
        print(f"⚠️  Ya existen {existing_recipes} recetas del sistema. ¿Deseas continuar? (s/n)")
        response = input().lower().strip()
        if response != 's':
            print("❌ Operación cancelada")
            return
        
        # Eliminar recetas existentes del sistema (con cascada manual)
        print("🗑️  Eliminando recetas existentes del sistema...")
        existing_recipes = RecipeORM.query.filter_by(user_uid=SYSTEM_USER_UID).all()
        for recipe in existing_recipes:
            # Eliminar ingredientes y pasos manualmente primero
            RecipeIngredientORM.query.filter_by(recipe_uid=recipe.uid).delete()
            RecipeStepORM.query.filter_by(recipe_uid=recipe.uid).delete()
            # Luego eliminar la receta
            db.session.delete(recipe)
        db.session.commit()
    
    # Inicializar servicio de generación de imágenes
    print("🎨 Inicializando servicio de generación de imágenes...")
    try:
        image_generator = make_recipe_image_generator_service()
        print("✅ Servicio de imágenes inicializado")
    except Exception as e:
        print(f"⚠️  Error inicializando servicio de imágenes: {str(e)}")
        image_generator = None
    
    total_recipes = 0
    successful_images = 0
    
    for category_name, recipes in RECIPES_DATA.items():
        print(f"\n📂 Procesando categoría: {category_name.upper()}")
        
        for recipe_data in recipes:
            recipe_uid = str(uuid.uuid4())
            
            print(f"   🔄 Procesando: {recipe_data['title']}")
            
            # Generar imagen para la receta
            image_url = None
            image_status = "pending"
            
            if image_generator:
                try:
                    print(f"      🎨 Generando imagen...")
                    
                    image_url = image_generator.get_or_generate_recipe_image(
                        recipe_title=recipe_data["title"],
                        user_uid=SYSTEM_USER_UID,
                        description=recipe_data["description"],
                        ingredients=recipe_data["ingredients"]
                    )
                    
                    if image_url and "placeholder" not in image_url.lower():
                        successful_images += 1
                        image_status = "completed"
                        print(f"      ✅ Imagen generada exitosamente")
                    else:
                        image_status = "fallback"
                        print(f"      ⚠️  Usando imagen fallback")
                        
                except Exception as e:
                    print(f"      ❌ Error generando imagen: {str(e)}")
                    image_url = f"https://via.placeholder.com/400x300/fde3e3/666666?text={recipe_data['title'].replace(' ', '+')}"
                    image_status = "fallback"
            else:
                image_url = f"https://via.placeholder.com/400x300/fde3e3/666666?text={recipe_data['title'].replace(' ', '+')}"
                image_status = "fallback"
            
            # Crear la receta principal
            recipe_orm = RecipeORM(
                uid=recipe_uid,
                user_uid=SYSTEM_USER_UID,
                title=recipe_data["title"],
                duration=recipe_data["duration"],
                difficulty=recipe_data["difficulty"],
                footer=recipe_data["footer"],
                generated_by_ai=False,  # Son recetas curadas, no generadas por IA
                saved_at=datetime.now(timezone.utc),
                generated_at=datetime.now(timezone.utc),
                image_status=image_status,
                category=recipe_data["category"],
                description=recipe_data["description"],
                image_path=image_url
            )
            
            db.session.add(recipe_orm)
            
            # Agregar ingredientes
            for ingredient in recipe_data["ingredients"]:
                ingredient_orm = RecipeIngredientORM(
                    recipe_uid=recipe_uid,
                    name=ingredient["name"],
                    quantity=ingredient["quantity"],
                    type_unit=ingredient["type_unit"]
                )
                db.session.add(ingredient_orm)
            
            # Agregar pasos
            for step in recipe_data["steps"]:
                step_orm = RecipeStepORM(
                    recipe_uid=recipe_uid,
                    step_order=step["step_order"],
                    description=step["description"]
                )
                db.session.add(step_orm)
            
            total_recipes += 1
            print(f"      ✅ Receta completada: {recipe_data['title']}")
    
    # Guardar todo en la base de datos
    try:
        db.session.commit()
        print(f"\n🎉 ¡ÉXITO COMPLETO!")
        print(f"📊 Estadísticas finales:")
        print(f"   • {total_recipes} recetas creadas")
        print(f"   • {successful_images} imágenes generadas con IA")
        print(f"   • {total_recipes - successful_images} imágenes fallback")
        print(f"📊 Distribución por categorías:")
        for category_name, recipes in RECIPES_DATA.items():
            print(f"   • {category_name}: {len(recipes)} recetas")
        print(f"🎨 Todas las recetas incluyen imágenes de alta calidad")
        print(f"📱 Disponibles en: /api/recipes/default")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error al guardar las recetas: {str(e)}")
        raise

def list_default_recipes():
    """Lista todas las recetas por defecto existentes"""
    
    recipes = RecipeORM.query.filter_by(user_uid=SYSTEM_USER_UID).all()
    
    if not recipes:
        print("📭 No hay recetas por defecto en la base de datos")
        return
    
    print(f"\n📚 RECETAS POR DEFECTO EXISTENTES ({len(recipes)} total):")
    print("=" * 60)
    
    # Agrupar por categoría
    by_category = {}
    for recipe in recipes:
        category = recipe.category
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(recipe)
    
    for category, category_recipes in by_category.items():
        print(f"\n📂 {category.upper()} ({len(category_recipes)} recetas):")
        for recipe in category_recipes:
            print(f"   • {recipe.title} ({recipe.difficulty}) - {recipe.duration}")

def delete_default_recipes():
    """Elimina todas las recetas por defecto"""
    
    recipes_count = RecipeORM.query.filter_by(user_uid=SYSTEM_USER_UID).count()
    
    if recipes_count == 0:
        print("📭 No hay recetas por defecto para eliminar")
        return
    
    print(f"⚠️  Se eliminarán {recipes_count} recetas por defecto. ¿Estás seguro? (s/n)")
    response = input().lower().strip()
    
    if response != 's':
        print("❌ Operación cancelada")
        return
    
    try:
        # Eliminar recetas con cascada manual
        recipes_to_delete = RecipeORM.query.filter_by(user_uid=SYSTEM_USER_UID).all()
        deleted_count = len(recipes_to_delete)
        
        for recipe in recipes_to_delete:
            # Eliminar ingredientes y pasos manualmente primero
            RecipeIngredientORM.query.filter_by(recipe_uid=recipe.uid).delete()
            RecipeStepORM.query.filter_by(recipe_uid=recipe.uid).delete()
            # Luego eliminar la receta
            db.session.delete(recipe)
        
        db.session.commit()
        print(f"✅ Se eliminaron {deleted_count} recetas por defecto")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error al eliminar las recetas: {str(e)}")
        raise

def main():
    """Función principal del script"""
    
    print("🍳 GENERADOR DE RECETAS POR DEFECTO - ZeroWasteAI")
    print("=" * 50)
    print("1. Crear recetas por defecto")
    print("2. Listar recetas existentes")
    print("3. Eliminar recetas por defecto")
    print("4. Salir")
    print("=" * 50)
    
    while True:
        option = input("\nSelecciona una opción (1-4): ").strip()
        
        if option == "1":
            create_default_recipes()
            break
        elif option == "2":
            list_default_recipes()
            break
        elif option == "3":
            delete_default_recipes()
            break
        elif option == "4":
            print("👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción inválida. Por favor selecciona 1, 2, 3 o 4")

if __name__ == "__main__":
    # Crear la aplicación Flask para acceder al contexto de la base de datos
    app = create_app()
    
    with app.app_context():
        main()