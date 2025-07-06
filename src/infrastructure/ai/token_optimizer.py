"""
Optimizador de tokens para servicios de IA - reduce costos y mejora velocidad
"""
import re
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class TokenMetrics:
    """Métricas de optimización de tokens"""
    original_tokens: int
    optimized_tokens: int
    reduction_percentage: float
    tokens_saved: int


class TokenOptimizer:
    """
    Optimizador inteligente de tokens para prompts y respuestas de IA
    
    Características:
    - Compresión de prompts manteniendo efectividad
    - Limitación inteligente de parámetros de entrada
    - Parsing optimizado de respuestas JSON
    - Métricas de ahorro de tokens
    """
    
    def __init__(self):
        self.visual_keywords = [
            "color", "textura", "forma", "tamaño", "fresco", "maduro", 
            "verde", "rojo", "amarillo", "grande", "pequeño", "redondo",
            "brillante", "opaco", "suave", "rugoso"
        ]
        
        self.essential_cooking_terms = [
            "cocinar", "hervir", "freír", "asar", "mezclar", "cortar",
            "picar", "condimentar", "sal", "pimienta", "aceite"
        ]
        
        # Patrones para limpieza rápida de respuestas
        self.json_cleaning_patterns = [
            (r'```json\s*', ''),
            (r'```\s*', ''),
            (r'\n\s*\n', '\n'),
            (r'//.*?\n', '\n'),  # Eliminar comentarios
            (r'/\*.*?\*/', ''),  # Eliminar comentarios multilínea
        ]
    
    def optimize_ingredient_list(self, ingredients: List[Dict[str, Any]], max_items: int = 8) -> List[Dict[str, Any]]:
        """
        Optimiza lista de ingredientes para reducir tokens en prompts
        
        Args:
            ingredients: Lista de ingredientes completa
            max_items: Máximo número de ingredientes a incluir
            
        Returns:
            Lista optimizada de ingredientes
        """
        if len(ingredients) <= max_items:
            return ingredients
        
        # Priorizar ingredientes por relevancia
        scored_ingredients = []
        for ingredient in ingredients:
            score = self._calculate_ingredient_relevance(ingredient)
            scored_ingredients.append((score, ingredient))
        
        # Ordenar por score y tomar los mejores
        scored_ingredients.sort(key=lambda x: x[0], reverse=True)
        optimized = [item[1] for item in scored_ingredients[:max_items]]
        
        print(f"🎯 [TOKEN OPT] Reduced ingredients from {len(ingredients)} to {len(optimized)}")
        return optimized
    
    def _calculate_ingredient_relevance(self, ingredient: Dict[str, Any]) -> float:
        """
        Calcula la relevancia de un ingrediente para optimización
        
        Args:
            ingredient: Diccionario con datos del ingrediente
            
        Returns:
            Score de relevancia (mayor = más relevante)
        """
        score = 0.0
        
        # Boost por cantidad (ingredientes con más cantidad son más relevantes)
        quantity = ingredient.get("quantity", 0)
        if quantity > 0:
            score += min(quantity / 10.0, 2.0)  # Max 2 puntos por cantidad
        
        # Boost por tipo de ingrediente (proteínas y vegetales principales)
        name = ingredient.get("name", "").lower()
        main_ingredients = ["pollo", "carne", "pescado", "tomate", "cebolla", "ajo", "papa"]
        if any(main in name for main in main_ingredients):
            score += 1.5
        
        # Boost por proximidad a vencer (ingredientes que expiran pronto)
        expiration = ingredient.get("expiration_time", 0)
        time_unit = ingredient.get("time_unit", "")
        if time_unit.lower() == "días" and expiration <= 3:
            score += 2.0  # Priorizar ingredientes que expiran pronto
        
        return score
    
    def optimize_descriptions(self, items: List[Dict[str, Any]], max_description_length: int = 80) -> List[Dict[str, Any]]:
        """
        Optimiza descripciones de ingredientes/comidas para reducir tokens
        
        Args:
            items: Lista de items con descripciones
            max_description_length: Longitud máxima de descripción
            
        Returns:
            Lista con descripciones optimizadas
        """
        optimized_items = []
        
        for item in items:
            optimized_item = item.copy()
            description = item.get("description", "")
            
            if len(description) > max_description_length:
                # Extraer solo palabras clave visuales y esenciales
                optimized_description = self._extract_essential_words(
                    description, max_description_length
                )
                optimized_item["description"] = optimized_description
                
            optimized_items.append(optimized_item)
        
        return optimized_items
    
    def _extract_essential_words(self, text: str, max_length: int) -> str:
        """
        Extrae palabras esenciales de un texto para mantener solo información relevante
        
        Args:
            text: Texto original
            max_length: Longitud máxima permitida
            
        Returns:
            Texto optimizado con palabras clave
        """
        words = text.lower().split()
        essential_words = []
        
        # Priorizar palabras clave visuales y culinarias
        for word in words:
            if (any(keyword in word for keyword in self.visual_keywords) or
                any(term in word for term in self.essential_cooking_terms) or
                len(word) <= 4):  # Palabras cortas suelen ser importantes
                essential_words.append(word)
        
        # Si no hay suficientes palabras clave, tomar las primeras palabras
        if len(" ".join(essential_words)) < max_length // 2:
            essential_words.extend(words[:15])  # Tomar primeras 15 palabras
        
        # Unir y recortar si es necesario
        result = " ".join(essential_words)
        if len(result) > max_length:
            result = result[:max_length].rsplit(' ', 1)[0] + "..."
        
        return result
    
    def compress_prompt(self, prompt: str, target_reduction: float = 0.3) -> str:
        """
        Comprime un prompt eliminando texto redundante manteniendo efectividad
        
        Args:
            prompt: Prompt original
            target_reduction: Porcentaje objetivo de reducción (0.3 = 30%)
            
        Returns:
            Prompt comprimido
        """
        original_length = len(prompt)
        
        # 1. Eliminar líneas vacías múltiples
        compressed = re.sub(r'\n\s*\n\s*\n', '\n\n', prompt)
        
        # 2. Eliminar espacios múltiples
        compressed = re.sub(r' +', ' ', compressed)
        
        # 3. Eliminar ejemplos redundantes (mantener solo 1-2)
        lines = compressed.split('\n')
        filtered_lines = []
        example_count = 0
        
        for line in lines:
            # Detectar líneas de ejemplo
            if any(marker in line.lower() for marker in ['ejemplo:', 'example:', '"title":', '"name":']):
                example_count += 1
                if example_count <= 2:  # Mantener solo 2 ejemplos
                    filtered_lines.append(line)
            else:
                filtered_lines.append(line)
        
        compressed = '\n'.join(filtered_lines)
        
        # 4. Simplificar instrucciones repetitivas
        compressed = self._simplify_redundant_instructions(compressed)
        
        current_reduction = (original_length - len(compressed)) / original_length
        
        print(f"🗜️ [TOKEN OPT] Compressed prompt: {original_length} → {len(compressed)} chars ({current_reduction:.1%} reduction)")
        
        return compressed
    
    def _simplify_redundant_instructions(self, text: str) -> str:
        """
        Simplifica instrucciones redundantes en prompts
        """
        # Patrones de texto redundante común
        redundant_patterns = [
            (r'Devuelve únicamente.*?JSON.*?sin.*?adicional.*?\n', 'Responde solo JSON.\n'),
            (r'No incluyas.*?saludos.*?código.*?texto.*?\n', ''),
            (r'Actúa como un.*?experto en.*?\n', 'Chef experto: '),
            (r'Recibirás.*?imagen.*?que.*?puede.*?contener.*?\n', 'Analiza imagen: '),
        ]
        
        for pattern, replacement in redundant_patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE | re.DOTALL)
        
        return text
    
    def fast_json_parse(self, response_text: str) -> Dict[str, Any]:
        """
        Parser JSON optimizado con limpieza automática
        
        Args:
            response_text: Texto de respuesta que contiene JSON
            
        Returns:
            Objeto JSON parseado
            
        Raises:
            ValueError: Si no se puede parsear el JSON
        """
        # Aplicar patrones de limpieza rápida
        cleaned = response_text.strip()
        
        for pattern, replacement in self.json_cleaning_patterns:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.DOTALL)
        
        # Encontrar JSON array o object
        json_start = max(cleaned.find('['), cleaned.find('{'))
        json_end = max(cleaned.rfind(']'), cleaned.rfind('}'))
        
        if json_start == -1 or json_end == -1:
            raise ValueError("No valid JSON structure found")
        
        json_text = cleaned[json_start:json_end + 1]
        
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            # Intentar reparación automática
            repaired = self._auto_repair_json(json_text)
            try:
                return json.loads(repaired)
            except:
                raise ValueError(f"Failed to parse JSON: {str(e)}")
    
    def _auto_repair_json(self, json_text: str) -> str:
        """
        Intenta reparar JSON malformado automáticamente
        """
        # Reparaciones comunes
        repairs = [
            # Comas faltantes entre objetos
            (r'}(\s*){', '},{'),
            # Comas finales
            (r',(\s*[}\]])', r'\1'),
            # Comillas faltantes en propiedades
            (r'(\w+):', r'"\1":'),
            # Comillas dobles en strings
            (r':\s*"([^"]*)"([^"]*)"', r': "\1\2"'),
        ]
        
        repaired = json_text
        for pattern, replacement in repairs:
            repaired = re.sub(pattern, replacement, repaired)
        
        return repaired
    
    def calculate_token_savings(self, original_text: str, optimized_text: str) -> TokenMetrics:
        """
        Calcula métricas de ahorro de tokens
        
        Args:
            original_text: Texto original
            optimized_text: Texto optimizado
            
        Returns:
            Métricas de optimización
        """
        # Estimación aproximada: 1 token ≈ 4 caracteres en español
        original_tokens = len(original_text) // 4
        optimized_tokens = len(optimized_text) // 4
        tokens_saved = original_tokens - optimized_tokens
        reduction_percentage = (tokens_saved / original_tokens) * 100 if original_tokens > 0 else 0
        
        return TokenMetrics(
            original_tokens=original_tokens,
            optimized_tokens=optimized_tokens,
            reduction_percentage=reduction_percentage,
            tokens_saved=tokens_saved
        )
    
    def optimize_generation_config(self, base_config: Dict[str, Any], optimization_level: str = "balanced") -> Dict[str, Any]:
        """
        Optimiza configuración de generación para balance velocidad/calidad
        
        Args:
            base_config: Configuración base
            optimization_level: "fast", "balanced", "quality"
            
        Returns:
            Configuración optimizada
        """
        configs = {
            "fast": {
                "temperature": 0.3,
                "max_output_tokens": 1024,
                "top_k": 20,
                "top_p": 0.8,
                "candidate_count": 1
            },
            "balanced": {
                "temperature": 0.5,
                "max_output_tokens": 2048,
                "top_k": 40,
                "top_p": 0.9,
                "candidate_count": 1
            },
            "quality": {
                "temperature": 0.7,
                "max_output_tokens": 4096,
                "top_k": 50,
                "top_p": 0.95,
                "candidate_count": 1
            }
        }
        
        optimized = base_config.copy()
        optimized.update(configs.get(optimization_level, configs["balanced"]))
        
        return optimized


# Instancia global del optimizador
token_optimizer = TokenOptimizer()