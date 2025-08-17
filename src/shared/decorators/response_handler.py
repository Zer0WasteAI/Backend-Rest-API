from functools import wraps
from flask import jsonify
from typing import Callable, Any, Tuple, Optional
import traceback

from src.shared.messages.response_messages import APIResponse, ServiceType, MessageType
from src.shared.exceptions.custom import (
    InvalidRequestDataException,
    RecipeNotFoundException,
    InvalidTokenException
)


def api_response(service: ServiceType, action: str):
    """
    Decorator para manejar respuestas de API con mensajes bonitos y contextuales.
    
    Args:
        service: Tipo de servicio (ServiceType.RECIPES, etc.)
        action: Acción específica ("upload", "create", etc.)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Tuple[dict, int]:
            try:
                # Ejecutar la función original
                result = func(*args, **kwargs)
                
                # Si la función ya retorna una tupla (data, status_code)
                if isinstance(result, tuple) and len(result) == 2:
                    data, status_code = result
                    return jsonify(*APIResponse.success(
                        service=service,
                        action=action,
                        data=data,
                        status_code=status_code
                    ))
                
                # Si solo retorna data
                else:
                    return jsonify(*APIResponse.success(
                        service=service,
                        action=action,
                        data=result
                    ))
                    
            except InvalidRequestDataException as e:
                return jsonify(*APIResponse.error(
                    service=service,
                    action=action,
                    error_details=str(e),
                    status_code=400,
                    custom_message=f"📝 Datos inválidos: {str(e)}"
                ))
                
            except RecipeNotFoundException as e:
                return jsonify(*APIResponse.not_found(
                    service=service,
                    resource="recipe",
                    custom_message=f"🍳 {str(e)}"
                ))
                
            except InvalidTokenException as e:
                return jsonify(*APIResponse.unauthorized(
                    service=service,
                    action=action,
                    custom_message=f"🔑 {str(e)}"
                ))
                
            except PermissionError as e:
                return jsonify(*APIResponse.unauthorized(
                    service=service,
                    action=action,
                    custom_message=f"🚫 Sin permisos: {str(e)}"
                ))
                
            except FileNotFoundError as e:
                return jsonify(*APIResponse.not_found(
                    service=service,
                    resource="file",
                    custom_message=f"📁 Archivo no encontrado: {str(e)}"
                ))
                
            except ValueError as e:
                return jsonify(*APIResponse.error(
                    service=service,
                    action=action,
                    error_details=str(e),
                    status_code=400,
                    custom_message=f"⚠️ Valor inválido: {str(e)}"
                ))
                
            except Exception as e:
                # Log del error completo para debugging
                print(f"🚨 [API ERROR] Service: {service.value}, Action: {action}")
                print(f"🚨 [API ERROR] Error: {str(e)}")
                print(f"🚨 [API ERROR] Traceback: {traceback.format_exc()}")
                
                return jsonify(*APIResponse.error(
                    service=service,
                    action=action,
                    error_details="Error interno del servidor",
                    status_code=500,
                    custom_message="😞 Algo salió mal. Nuestro equipo ha sido notificado"
                ))
                
        return wrapper
    return decorator


def handle_auth_required(service: ServiceType, action: str = "access"):
    """
    Decorator específico para endpoints que requieren autenticación.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except InvalidTokenException as e:
                return jsonify(*APIResponse.unauthorized(
                    service=service,
                    action=action,
                    custom_message="🔑 Tu sesión ha expirado. Por favor, inicia sesión nuevamente"
                ))
            except PermissionError as e:
                return jsonify(*APIResponse.unauthorized(
                    service=service,
                    action=action,
                    custom_message="🚫 No tienes permisos para realizar esta acción"
                ))
        return wrapper
    return decorator


class ResponseHelper:
    """
    Clase auxiliar para generar respuestas rápidas sin decorator.
    Útil para casos donde necesitas control manual.
    """
    
    @staticmethod
    def success_response(service: ServiceType, action: str, data: Any = None, message: Optional[str] = None):
        """Respuesta de éxito rápida"""
        return jsonify(*APIResponse.success(
            service=service,
            action=action,
            data=data,
            custom_message=message
        ))
    
    @staticmethod
    def error_response(service: ServiceType, action: str, error: str, status_code: int = 400):
        """Respuesta de error rápida"""
        return jsonify(*APIResponse.error(
            service=service,
            action=action,
            error_details=error,
            status_code=status_code
        ))
    
    @staticmethod
    def not_found_response(service: ServiceType, resource: str, message: Optional[str] = None):
        """Respuesta de no encontrado rápida"""
        return jsonify(*APIResponse.not_found(
            service=service,
            resource=resource,
            custom_message=message
        ))
    
    @staticmethod
    def unauthorized_response(service: ServiceType, action: str = "access", message: Optional[str] = None):
        """Respuesta de no autorizado rápida"""
        return jsonify(*APIResponse.unauthorized(
            service=service,
            action=action,
            custom_message=message
        ))