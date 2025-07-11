from flask import Blueprint, jsonify
from src.infrastructure.db.token_security_repository import TokenSecurityRepository
from src.shared.decorators.internal_only import internal_only
from src.infrastructure.security.rate_limiter import api_rate_limit
from src.infrastructure.security.security_logger import security_logger, SecurityEventType
from flasgger import swag_from

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/cleanup-tokens', methods=['POST'])
@internal_only
@api_rate_limit
@swag_from({
    'tags': ['Admin'],
    'summary': 'Limpieza de tokens expirados',
    'description': 'Elimina tokens expirados de la blacklist y tracking (solo uso interno)',
    'security': [{'Internal-Secret': []}],
    'responses': {
        200: {'description': 'Limpieza completada exitosamente'},
        403: {'description': 'No autorizado - requiere secret interno'}
    }
})
def cleanup_expired_tokens():
    """Endpoint interno para limpiar tokens expirados"""
    try:
        token_repo = TokenSecurityRepository()
        result = token_repo.cleanup_expired_tokens()
        
        security_logger.log_security_event(
            SecurityEventType.TOKEN_BLACKLISTED,
            {
                "action": "cleanup_expired_tokens",
                "blacklist_cleaned": result["blacklist_cleaned"],
                "tracking_cleaned": result["tracking_cleaned"]
            }
        )
        
        return jsonify({
            "message": "Token cleanup completed successfully",
            "cleaned": result
        }), 200
        
    except Exception as e:
        security_logger.log_security_event(
            SecurityEventType.AUTHENTICATION_FAILED,
            {"endpoint": "cleanup-tokens", "reason": "cleanup_failed", "error": str(type(e).__name__)}
        )
        return jsonify({"error": "Cleanup operation failed"}), 500

@admin_bp.route('/security-stats', methods=['GET'])
@internal_only
@api_rate_limit
@swag_from({
    'tags': ['Admin'],
    'summary': 'Estadísticas de seguridad',
    'description': 'Obtiene estadísticas de tokens activos y blacklisted (solo uso interno)',
    'security': [{'Internal-Secret': []}],
    'responses': {
        200: {'description': 'Estadísticas obtenidas exitosamente'},
        403: {'description': 'No autorizado'}
    }
})
def get_security_stats():
    """Endpoint interno para obtener estadísticas de seguridad"""
    try:
        from src.infrastructure.db.schemas.token_blacklist_schema import TokenBlacklist, RefreshTokenTracking
        from src.infrastructure.db.base import db
        
        # Contar tokens en blacklist
        blacklisted_count = db.session.query(TokenBlacklist).count()
        
        # Contar refresh tokens activos
        active_refresh_tokens = db.session.query(RefreshTokenTracking).filter_by(used=False).count()
        
        # Contar refresh tokens usados
        used_refresh_tokens = db.session.query(RefreshTokenTracking).filter_by(used=True).count()
        
        return jsonify({
            "security_stats": {
                "blacklisted_tokens": blacklisted_count,
                "active_refresh_tokens": active_refresh_tokens,
                "used_refresh_tokens": used_refresh_tokens,
                "total_refresh_tokens": active_refresh_tokens + used_refresh_tokens
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": "Failed to get security stats"}), 500 