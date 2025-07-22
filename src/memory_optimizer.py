"""
Optimizador de memoria para el sistema de generación de preguntas PDF.
Diseñado para funcionar eficientemente con 4GB de RAM.
"""
import gc
import torch
import psutil
import logging
from typing import Optional, Dict, Any
import os

class MemoryOptimizer:
    """Clase para gestionar y optimizar el uso de memoria."""
    
    def __init__(self, max_memory_gb: float = 3.5):
        """
        Inicializa el optimizador de memoria.
        
        Args:
            max_memory_gb: Límite máximo de memoria en GB (por defecto 3.5GB para sistema de 4GB)
        """
        self.max_memory_gb = max_memory_gb
        self.max_memory_bytes = max_memory_gb * 1024 * 1024 * 1024
        self.setup_logging()
        self.configure_environment()
    
    def setup_logging(self):
        """Configura el logging para seguimiento de memoria."""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def configure_environment(self):
        """Configura variables de entorno para optimización de memoria."""
        # Limitar threads de PyTorch
        torch.set_num_threads(2)
        
        # Configurar cache de Transformers
        os.environ['TRANSFORMERS_CACHE'] = './models'
        os.environ['TORCH_HOME'] = './models'
        
        # Deshabilitar warnings innecesarios
        os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    
    def get_memory_usage(self) -> Dict[str, float]:
        """
        Obtiene el uso actual de memoria del sistema y proceso.
        
        Returns:
            Dict con información de memoria en MB
        """
        process = psutil.Process()
        system_memory = psutil.virtual_memory()
        
        return {
            'process_memory_mb': process.memory_info().rss / 1024 / 1024,
            'system_memory_percent': system_memory.percent,
            'system_available_mb': system_memory.available / 1024 / 1024,
            'system_total_mb': system_memory.total / 1024 / 1024
        }
    
    def check_memory_limit(self) -> bool:
        """
        Verifica si el uso de memoria está cerca del límite.
        
        Returns:
            True si hay suficiente memoria disponible
        """
        memory_info = self.get_memory_usage()
        
        if memory_info['process_memory_mb'] > (self.max_memory_gb * 1024 * 0.9):
            self.logger.warning(f"Memoria del proceso cerca del límite: {memory_info['process_memory_mb']:.1f}MB")
            return False
        
        if memory_info['system_memory_percent'] > 90:
            self.logger.warning(f"Memoria del sistema alta: {memory_info['system_memory_percent']:.1f}%")
            return False
        
        return True
    
    def cleanup_memory(self, force: bool = False):
        """
        Realiza limpieza de memoria.
        
        Args:
            force: Fuerza limpieza intensiva
        """
        if force or not self.check_memory_limit():
            self.logger.info("Iniciando limpieza de memoria...")
            
            # Garbage collection
            gc.collect()
            
            # Limpiar cache de PyTorch si hay GPU
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Log del estado después de limpieza
            memory_info = self.get_memory_usage()
            self.logger.info(f"Memoria después de limpieza: {memory_info['process_memory_mb']:.1f}MB")
    
    def monitor_memory_usage(self, operation_name: str = ""):
        """
        Decorator para monitorear uso de memoria en operaciones.
        
        Args:
            operation_name: Nombre de la operación para logging
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Memoria antes
                memory_before = self.get_memory_usage()
                self.logger.info(f"[{operation_name}] Memoria antes: {memory_before['process_memory_mb']:.1f}MB")
                
                # Ejecutar función
                result = func(*args, **kwargs)
                
                # Memoria después
                memory_after = self.get_memory_usage()
                memory_diff = memory_after['process_memory_mb'] - memory_before['process_memory_mb']
                
                self.logger.info(f"[{operation_name}] Memoria después: {memory_after['process_memory_mb']:.1f}MB (Δ: {memory_diff:+.1f}MB)")
                
                # Limpieza automática si es necesario
                if not self.check_memory_limit():
                    self.cleanup_memory()
                
                return result
            return wrapper
        return decorator
    
    def get_optimal_batch_size(self, base_batch_size: int = 4) -> int:
        """
        Calcula el tamaño de batch óptimo basado en la memoria disponible.
        
        Args:
            base_batch_size: Tamaño base de batch
            
        Returns:
            Tamaño de batch optimizado
        """
        memory_info = self.get_memory_usage()
        available_memory_gb = memory_info['system_available_mb'] / 1024
        
        # Ajustar batch size según memoria disponible
        if available_memory_gb < 1.0:
            return 1
        elif available_memory_gb < 2.0:
            return max(1, base_batch_size // 2)
        else:
            return base_batch_size
    
    def get_optimal_chunk_size(self, document_length: int, base_chunk_size: int = 512) -> int:
        """
        Calcula el tamaño de chunk óptimo para procesar documentos.
        
        Args:
            document_length: Longitud del documento en tokens
            base_chunk_size: Tamaño base de chunk
            
        Returns:
            Tamaño de chunk optimizado
        """
        memory_info = self.get_memory_usage()
        
        # Reducir chunk size si la memoria está limitada
        if memory_info['system_memory_percent'] > 80:
            return base_chunk_size // 2
        elif memory_info['system_memory_percent'] > 90:
            return base_chunk_size // 4
        else:
            return base_chunk_size

# Instancia global del optimizador
memory_optimizer = MemoryOptimizer()
