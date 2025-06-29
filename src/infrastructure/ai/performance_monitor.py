"""
Sistema de monitoreo de rendimiento para servicios de IA
Tracks metrics, response times, cache hits, token usage, and more
"""
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import threading


@dataclass
class PerformanceMetric:
    """Métrica individual de rendimiento"""
    operation: str
    start_time: float
    end_time: float
    duration: float
    success: bool
    cache_hit: bool
    tokens_used: int
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PerformanceStats:
    """Estadísticas agregadas de rendimiento"""
    operation: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    cache_hits: int
    cache_misses: int
    average_duration: float
    min_duration: float
    max_duration: float
    total_tokens: int
    average_tokens: float
    success_rate: float
    cache_hit_rate: float
    last_24h_requests: int


class PerformanceMonitor:
    """
    Monitor de rendimiento para servicios de IA con métricas en tiempo real
    
    Características:
    - Tracking automático de tiempos de respuesta
    - Métricas de cache hits/misses
    - Uso de tokens y costos estimados
    - Alertas de rendimiento
    - Histórico de 24 horas
    - Thread-safe
    """
    
    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self.active_operations: Dict[str, float] = {}
        self.stats_cache: Dict[str, PerformanceStats] = {}
        self.lock = threading.Lock()
        
        # Configuración de alertas
        self.alert_thresholds = {
            'max_duration': 30.0,      # Segundos
            'min_success_rate': 0.85,  # 85%
            'max_token_usage': 5000,   # Tokens por request
        }
        
        # Cleanup automático (mantener solo últimas 24h)
        self.max_age_hours = 24
        
    def start_operation(self, operation_id: str, operation_type: str) -> str:
        """
        Inicia el tracking de una operación
        
        Args:
            operation_id: ID único de la operación
            operation_type: Tipo de operación (ej: 'recipe_generation', 'ingredient_recognition')
            
        Returns:
            operation_id para referencia
        """
        with self.lock:
            self.active_operations[operation_id] = {
                'start_time': time.time(),
                'operation_type': operation_type
            }
        
        print(f"📊 [MONITOR] Started tracking: {operation_type} ({operation_id})")
        return operation_id
    
    def end_operation(self, operation_id: str, success: bool = True, 
                     cache_hit: bool = False, tokens_used: int = 0,
                     error_message: Optional[str] = None, 
                     metadata: Optional[Dict[str, Any]] = None) -> PerformanceMetric:
        """
        Finaliza el tracking de una operación y registra métricas
        
        Args:
            operation_id: ID de la operación
            success: Si la operación fue exitosa
            cache_hit: Si se utilizó cache
            tokens_used: Tokens consumidos
            error_message: Mensaje de error (si aplica)
            metadata: Metadatos adicionales
            
        Returns:
            PerformanceMetric con los datos registrados
        """
        end_time = time.time()
        
        with self.lock:
            if operation_id not in self.active_operations:
                print(f"⚠️ [MONITOR] Operation {operation_id} not found in active operations")
                return None
            
            operation_data = self.active_operations.pop(operation_id)
            start_time = operation_data['start_time']
            operation_type = operation_data['operation_type']
            duration = end_time - start_time
            
            # Crear métrica
            metric = PerformanceMetric(
                operation=operation_type,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                success=success,
                cache_hit=cache_hit,
                tokens_used=tokens_used,
                error_message=error_message,
                metadata=metadata or {}
            )
            
            # Almacenar métrica
            self.metrics.append(metric)
            
            # Limpiar métricas antiguas
            self._cleanup_old_metrics()
            
            # Invalidar cache de estadísticas
            if operation_type in self.stats_cache:
                del self.stats_cache[operation_type]
            
            # Check alertas
            self._check_alerts(metric)
            
            status = "SUCCESS" if success else "FAILED"
            cache_status = "CACHE HIT" if cache_hit else "CACHE MISS"
            
            print(f"📊 [MONITOR] {operation_type}: {duration:.2f}s, {status}, {cache_status}, {tokens_used} tokens")
            
            return metric
    
    def get_stats(self, operation_type: Optional[str] = None) -> Dict[str, PerformanceStats]:
        """
        Obtiene estadísticas de rendimiento
        
        Args:
            operation_type: Tipo específico de operación (None para todas)
            
        Returns:
            Diccionario con estadísticas por tipo de operación
        """
        with self.lock:
            if operation_type and operation_type in self.stats_cache:
                return {operation_type: self.stats_cache[operation_type]}
            
            stats = {}
            operations = [operation_type] if operation_type else list(set(m.operation for m in self.metrics))
            
            for op_type in operations:
                stats[op_type] = self._calculate_stats(op_type)
                self.stats_cache[op_type] = stats[op_type]
            
            return stats
    
    def _calculate_stats(self, operation_type: str) -> PerformanceStats:
        """Calcula estadísticas para un tipo de operación"""
        
        # Filtrar métricas del tipo especificado
        op_metrics = [m for m in self.metrics if m.operation == operation_type]
        
        if not op_metrics:
            return PerformanceStats(
                operation=operation_type,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                cache_hits=0,
                cache_misses=0,
                average_duration=0.0,
                min_duration=0.0,
                max_duration=0.0,
                total_tokens=0,
                average_tokens=0.0,
                success_rate=0.0,
                cache_hit_rate=0.0,
                last_24h_requests=0
            )
        
        # Calcular estadísticas
        total_requests = len(op_metrics)
        successful_requests = sum(1 for m in op_metrics if m.success)
        failed_requests = total_requests - successful_requests
        cache_hits = sum(1 for m in op_metrics if m.cache_hit)
        cache_misses = total_requests - cache_hits
        
        durations = [m.duration for m in op_metrics]
        tokens = [m.tokens_used for m in op_metrics]
        
        # Requests en últimas 24h
        cutoff_time = time.time() - (24 * 3600)
        last_24h_requests = sum(1 for m in op_metrics if m.end_time >= cutoff_time)
        
        return PerformanceStats(
            operation=operation_type,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            average_duration=sum(durations) / len(durations),
            min_duration=min(durations),
            max_duration=max(durations),
            total_tokens=sum(tokens),
            average_tokens=sum(tokens) / len(tokens) if tokens else 0,
            success_rate=successful_requests / total_requests,
            cache_hit_rate=cache_hits / total_requests if total_requests > 0 else 0,
            last_24h_requests=last_24h_requests
        )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen completo de rendimiento
        
        Returns:
            Resumen con métricas principales y alertas
        """
        with self.lock:
            all_stats = self.get_stats()
            
            # Métricas agregadas
            total_requests = sum(stats.total_requests for stats in all_stats.values())
            total_cache_hits = sum(stats.cache_hits for stats in all_stats.values())
            total_tokens = sum(stats.total_tokens for stats in all_stats.values())
            
            # Promedios ponderados
            avg_duration = 0
            avg_success_rate = 0
            avg_cache_hit_rate = 0
            
            if total_requests > 0:
                avg_duration = sum(
                    stats.average_duration * stats.total_requests 
                    for stats in all_stats.values()
                ) / total_requests
                
                avg_success_rate = sum(
                    stats.success_rate * stats.total_requests 
                    for stats in all_stats.values()
                ) / total_requests
                
                avg_cache_hit_rate = total_cache_hits / total_requests
            
            # Alertas activas
            active_alerts = self._get_active_alerts()
            
            return {
                "summary": {
                    "total_requests": total_requests,
                    "average_duration": round(avg_duration, 2),
                    "average_success_rate": round(avg_success_rate, 3),
                    "cache_hit_rate": round(avg_cache_hit_rate, 3),
                    "total_tokens_used": total_tokens,
                    "estimated_cost_usd": round(total_tokens * 0.00002, 4),
                    "active_operations": len(self.active_operations),
                    "metrics_stored": len(self.metrics)
                },
                "by_operation": {op: asdict(stats) for op, stats in all_stats.items()},
                "alerts": active_alerts,
                "health_status": "healthy" if not active_alerts else "warning"
            }
    
    def _cleanup_old_metrics(self):
        """Limpia métricas antiguas para mantener solo las últimas 24h"""
        cutoff_time = time.time() - (self.max_age_hours * 3600)
        old_count = len(self.metrics)
        self.metrics = [m for m in self.metrics if m.end_time >= cutoff_time]
        
        if len(self.metrics) < old_count:
            print(f"🧹 [MONITOR] Cleaned {old_count - len(self.metrics)} old metrics")
    
    def _check_alerts(self, metric: PerformanceMetric):
        """Verifica si una métrica dispara alertas"""
        alerts = []
        
        # Alerta por duración larga
        if metric.duration > self.alert_thresholds['max_duration']:
            alerts.append(f"Slow operation: {metric.operation} took {metric.duration:.2f}s")
        
        # Alerta por uso excesivo de tokens
        if metric.tokens_used > self.alert_thresholds['max_token_usage']:
            alerts.append(f"High token usage: {metric.operation} used {metric.tokens_used} tokens")
        
        # Alerta por fallo
        if not metric.success:
            alerts.append(f"Operation failed: {metric.operation} - {metric.error_message}")
        
        for alert in alerts:
            print(f"🚨 [ALERT] {alert}")
    
    def _get_active_alerts(self) -> List[str]:
        """Obtiene alertas activas basadas en estadísticas recientes"""
        alerts = []
        
        # Verificar últimas 10 operaciones de cada tipo
        recent_window = time.time() - 300  # Últimos 5 minutos
        recent_metrics = [m for m in self.metrics if m.end_time >= recent_window]
        
        operations = set(m.operation for m in recent_metrics)
        
        for operation in operations:
            op_metrics = [m for m in recent_metrics if m.operation == operation]
            
            if len(op_metrics) >= 3:  # Suficientes datos para alertas
                success_rate = sum(1 for m in op_metrics if m.success) / len(op_metrics)
                avg_duration = sum(m.duration for m in op_metrics) / len(op_metrics)
                
                if success_rate < self.alert_thresholds['min_success_rate']:
                    alerts.append(f"Low success rate for {operation}: {success_rate:.2%}")
                
                if avg_duration > self.alert_thresholds['max_duration']:
                    alerts.append(f"High average duration for {operation}: {avg_duration:.2f}s")
        
        return alerts
    
    def export_metrics(self, operation_type: Optional[str] = None, 
                      hours_back: int = 24) -> List[Dict[str, Any]]:
        """
        Exporta métricas para análisis externo
        
        Args:
            operation_type: Filtrar por tipo de operación
            hours_back: Horas hacia atrás a incluir
            
        Returns:
            Lista de métricas en formato diccionario
        """
        cutoff_time = time.time() - (hours_back * 3600)
        
        with self.lock:
            filtered_metrics = [
                m for m in self.metrics 
                if m.end_time >= cutoff_time and (
                    operation_type is None or m.operation == operation_type
                )
            ]
            
            return [
                {
                    "operation": m.operation,
                    "timestamp": datetime.fromtimestamp(m.end_time).isoformat(),
                    "duration": m.duration,
                    "success": m.success,
                    "cache_hit": m.cache_hit,
                    "tokens_used": m.tokens_used,
                    "error_message": m.error_message,
                    "metadata": m.metadata
                }
                for m in filtered_metrics
            ]
    
    def reset_metrics(self):
        """Limpia todas las métricas almacenadas"""
        with self.lock:
            old_count = len(self.metrics)
            self.metrics.clear()
            self.active_operations.clear()
            self.stats_cache.clear()
            print(f"🗑️ [MONITOR] Reset: Cleared {old_count} metrics")


# Instancia global del monitor
performance_monitor = PerformanceMonitor()


# Context manager para facilitar el uso
class OperationTracker:
    """Context manager para tracking automático de operaciones"""
    
    def __init__(self, operation_type: str, metadata: Optional[Dict[str, Any]] = None):
        self.operation_type = operation_type
        self.metadata = metadata or {}
        self.operation_id = None
        self.tokens_used = 0
        self.cache_hit = False
        
    def __enter__(self):
        import uuid
        self.operation_id = f"{self.operation_type}_{uuid.uuid4().hex[:8]}"
        performance_monitor.start_operation(self.operation_id, self.operation_type)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        success = exc_type is None
        error_message = str(exc_val) if exc_val else None
        
        performance_monitor.end_operation(
            self.operation_id,
            success=success,
            cache_hit=self.cache_hit,
            tokens_used=self.tokens_used,
            error_message=error_message,
            metadata=self.metadata
        )
    
    def set_cache_hit(self, cache_hit: bool):
        """Marca si se utilizó cache"""
        self.cache_hit = cache_hit
    
    def set_tokens_used(self, tokens: int):
        """Establece el número de tokens utilizados"""
        self.tokens_used = tokens