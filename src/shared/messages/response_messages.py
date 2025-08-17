from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime


class MessageType(Enum):
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ServiceType(Enum):
    AUTH = "authentication"
    RECIPES = "recipes"
    INVENTORY = "inventory"
    COOKING = "cooking_session"
    RECOGNITION = "recognition"
    IMAGES = "image_management"
    PLANNING = "meal_planning"
    ENVIRONMENTAL = "environmental_savings"
    USER = "user_profile"
    ADMIN = "admin"


class ResponseMessages:
    """
    Sistema centralizado de mensajes bonitos y contextuales para la API.
    Cada servicio tiene sus propios mensajes personalizados.
    """
    
    # 🔐 AUTHENTICATION MESSAGES
    AUTH_MESSAGES = {
        "success": {
            "login": "¡Bienvenido de vuelta! 🎉 Has iniciado sesión exitosamente",
            "logout": "¡Hasta pronto! 👋 Has cerrado sesión de forma segura",
            "token_refresh": "🔄 Token renovado exitosamente. Tu sesión sigue activa",
            "firebase_signin": "🔥 Autenticación con Firebase completada exitosamente"
        },
        "error": {
            "invalid_credentials": "❌ Credenciales incorrectas. Verifica tu email y contraseña",
            "token_expired": "⏰ Tu sesión ha expirado. Por favor, inicia sesión nuevamente",
            "unauthorized": "🚫 No tienes autorización para acceder a este recurso",
            "invalid_token": "🔑 Token inválido o malformado",
            "firebase_error": "🔥 Error en la autenticación con Firebase"
        }
    }
    
    # 🍳 RECIPES MESSAGES
    RECIPES_MESSAGES = {
        "success": {
            "generated": "✨ ¡Receta generada con éxito! Tu nueva creación culinaria está lista",
            "saved": "💾 Receta guardada en tus favoritos. ¡Ya puedes cocinarla cuando quieras!",
            "deleted": "🗑️ Receta eliminada correctamente de tu colección",
            "favorite_added": "❤️ Receta añadida a tus favoritas. ¡Excelente elección!",
            "favorite_removed": "💔 Receta eliminada de favoritas",
            "list_retrieved": "📋 Lista de recetas obtenida exitosamente"
        },
        "error": {
            "not_found": "🔍 No encontramos esa receta. ¿Estás seguro que existe?",
            "generation_failed": "😞 No pudimos generar la receta. Inténtalo nuevamente",
            "save_failed": "💥 Error al guardar la receta. Revisa tu conexión",
            "already_favorite": "💡 Esta receta ya está en tus favoritas",
            "invalid_ingredients": "🥕 Los ingredientes proporcionados no son válidos"
        }
    }
    
    # 📦 INVENTORY MESSAGES
    INVENTORY_MESSAGES = {
        "success": {
            "item_added": "✅ ¡Genial! Ingrediente agregado a tu inventario inteligente",
            "item_updated": "🔄 Información del ingrediente actualizada correctamente",
            "item_deleted": "🗑️ Ingrediente eliminado de tu inventario",
            "quantity_updated": "📊 Cantidad actualizada. Tu inventario está al día",
            "batch_managed": "📦 Lote gestionado exitosamente con sistema FEFO",
            "expiring_retrieved": "⏰ Lista de productos próximos a vencer obtenida",
            "inventory_synced": "🔄 Inventario sincronizado correctamente"
        },
        "error": {
            "item_not_found": "🔍 No encontramos ese ingrediente en tu inventario",
            "insufficient_quantity": "⚠️ Cantidad insuficiente para esta operación",
            "expired_item": "⏰ Este ingrediente ya ha expirado y no puede usarse",
            "invalid_quantity": "📊 La cantidad ingresada no es válida",
            "batch_error": "📦 Error en la gestión de lotes. Verifica los datos"
        }
    }
    
    # 👨‍🍳 COOKING SESSION MESSAGES
    COOKING_MESSAGES = {
        "success": {
            "session_started": "🔥 ¡Sesión de cocina iniciada! Que disfrutes cocinando",
            "step_completed": "✅ Paso completado exitosamente. ¡Vas muy bien!",
            "session_finished": "🎉 ¡Felicitaciones! Has terminado de cocinar tu deliciosa receta",
            "mise_en_place": "📝 Mise en place preparado. Todo listo para cocinar"
        },
        "error": {
            "session_not_found": "🔍 No encontramos esa sesión de cocina",
            "session_limit": "⚠️ Has alcanzado el límite máximo de sesiones activas",
            "invalid_step": "❌ Paso de cocina inválido o ya completado",
            "ingredients_unavailable": "🥕 Algunos ingredientes no están disponibles en tu inventario"
        }
    }
    
    # 🤖 RECOGNITION MESSAGES
    RECOGNITION_MESSAGES = {
        "success": {
            "image_processed": "📸 ¡Imagen procesada exitosamente! Hemos identificado tus alimentos",
            "ingredients_recognized": "🔍 Ingredientes reconocidos con inteligencia artificial",
            "batch_processed": "📦 Lote de imágenes procesado correctamente",
            "foods_identified": "🍽️ Alimentos identificados exitosamente"
        },
        "error": {
            "image_not_clear": "📷 La imagen no es clara. Intenta con mejor iluminación",
            "no_food_detected": "🤔 No detectamos alimentos en esta imagen",
            "processing_failed": "⚠️ Error al procesar la imagen. Inténtalo nuevamente",
            "unsupported_format": "📁 Formato de imagen no soportado"
        }
    }
    
    # 📸 IMAGE MANAGEMENT MESSAGES
    IMAGES_MESSAGES = {
        "success": {
            "uploaded": "📸 ¡Imagen subida exitosamente! Ya está disponible en tu galería",
            "assigned": "🎯 Imagen asignada correctamente al ingrediente",
            "similar_found": "🔍 Imágenes similares encontradas en nuestra base de datos",
            "synced": "🔄 Imágenes sincronizadas correctamente"
        },
        "error": {
            "upload_failed": "📷 Error al subir la imagen. Verifica el archivo",
            "invalid_format": "📁 Formato de imagen no válido. Usa JPG, PNG o WebP",
            "file_too_large": "📏 La imagen es demasiado grande. Máximo 10MB",
            "no_image_found": "🔍 No se encontró ninguna imagen similar"
        }
    }
    
    # 📅 MEAL PLANNING MESSAGES
    PLANNING_MESSAGES = {
        "success": {
            "plan_saved": "📅 ¡Plan de comidas guardado! Tu semana está organizada",
            "plan_updated": "🔄 Plan de comidas actualizado exitosamente",
            "plan_deleted": "🗑️ Plan eliminado de tu calendario",
            "plans_retrieved": "📋 Planes de comida obtenidos correctamente"
        },
        "error": {
            "plan_not_found": "📅 No encontramos ese plan de comidas",
            "date_conflict": "⚠️ Ya tienes un plan para esa fecha",
            "invalid_date": "📆 Fecha inválida para el plan de comidas",
            "planning_failed": "😞 Error al crear el plan de comidas"
        }
    }
    
    # 🌱 ENVIRONMENTAL MESSAGES
    ENVIRONMENTAL_MESSAGES = {
        "success": {
            "savings_calculated": "🌱 ¡Impacto ambiental calculado! Estás ayudando al planeta",
            "impact_saved": "💚 Datos de sostenibilidad guardados correctamente",
            "summary_generated": "📊 Resumen ambiental generado exitosamente"
        },
        "error": {
            "calculation_failed": "🌍 Error al calcular el impacto ambiental",
            "data_insufficient": "📊 Datos insuficientes para el cálculo ambiental",
            "environmental_error": "🌱 Error en el servicio de sostenibilidad"
        }
    }
    
    # 👤 USER PROFILE MESSAGES
    USER_MESSAGES = {
        "success": {
            "profile_updated": "👤 ¡Perfil actualizado exitosamente! Cambios guardados",
            "profile_retrieved": "📋 Información de perfil obtenida correctamente",
            "preferences_saved": "⚙️ Preferencias guardadas. Tu experiencia será personalizada"
        },
        "error": {
            "profile_not_found": "👤 No se encontró el perfil del usuario",
            "update_failed": "❌ Error al actualizar el perfil",
            "invalid_data": "📝 Datos de perfil inválidos"
        }
    }
    
    # 🛡️ ADMIN MESSAGES
    ADMIN_MESSAGES = {
        "success": {
            "tokens_cleaned": "🧹 Tokens limpiados exitosamente",
            "stats_retrieved": "📊 Estadísticas de seguridad obtenidas",
            "operation_completed": "✅ Operación administrativa completada"
        },
        "error": {
            "unauthorized_admin": "🚫 No tienes permisos de administrador",
            "operation_failed": "❌ Falló la operación administrativa",
            "invalid_admin_request": "⚠️ Solicitud administrativa inválida"
        }
    }

    @staticmethod
    def get_message(service: ServiceType, message_type: MessageType, action: str) -> str:
        """
        Obtiene un mensaje contextual para un servicio y acción específica.
        
        Args:
            service: Tipo de servicio (AUTH, RECIPES, etc.)
            message_type: Tipo de mensaje (SUCCESS, ERROR, etc.)
            action: Acción específica (login, upload, etc.)
        
        Returns:
            Mensaje contextual bonito
        """
        service_messages = getattr(ResponseMessages, f"{service.name}_MESSAGES", {})
        message_dict = service_messages.get(message_type.value, {})
        
        # Buscar mensaje específico o usar mensaje genérico
        message = message_dict.get(action, ResponseMessages._get_generic_message(message_type, action))
        
        return message
    
    @staticmethod
    def _get_generic_message(message_type: MessageType, action: str) -> str:
        """Mensajes genéricos como fallback"""
        generic_messages = {
            MessageType.SUCCESS: f"✅ Operación '{action}' completada exitosamente",
            MessageType.ERROR: f"❌ Error en la operación '{action}'",
            MessageType.WARNING: f"⚠️ Advertencia en '{action}'",
            MessageType.INFO: f"ℹ️ Información sobre '{action}'"
        }
        return generic_messages.get(message_type, f"Operación '{action}' procesada")


class APIResponse:
    """
    Generador de respuestas estandarizadas para la API con mensajes bonitos.
    """
    
    @staticmethod
    def success(
        service: ServiceType,
        action: str,
        data: Any = None,
        status_code: int = 200,
        custom_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generar respuesta de éxito"""
        message = custom_message or ResponseMessages.get_message(service, MessageType.SUCCESS, action)
        
        response = {
            "success": True,
            "message": message,
            "service": service.value,
            "action": action,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if data is not None:
            response["data"] = data
            
        return response, status_code
    
    @staticmethod
    def error(
        service: ServiceType,
        action: str,
        error_details: Optional[str] = None,
        status_code: int = 400,
        custom_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generar respuesta de error"""
        message = custom_message or ResponseMessages.get_message(service, MessageType.ERROR, action)
        
        response = {
            "success": False,
            "message": message,
            "service": service.value,
            "action": action,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if error_details:
            response["error_details"] = error_details
            
        return response, status_code
    
    @staticmethod
    def unauthorized(
        service: ServiceType,
        action: str = "access",
        custom_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generar respuesta de no autorizado"""
        message = custom_message or "🚫 No tienes autorización para realizar esta acción"
        
        response = {
            "success": False,
            "message": message,
            "service": service.value,
            "action": action,
            "error_type": "unauthorized",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        return response, 401
    
    @staticmethod
    def not_found(
        service: ServiceType,
        resource: str,
        custom_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generar respuesta de recurso no encontrado"""
        message = custom_message or f"🔍 No se encontró el recurso '{resource}' solicitado"
        
        response = {
            "success": False,
            "message": message,
            "service": service.value,
            "action": "find",
            "resource": resource,
            "error_type": "not_found",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        return response, 404