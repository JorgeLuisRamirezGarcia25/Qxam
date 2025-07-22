"""
Archivo __init__.py para el paquete src.
Hace que src sea un paquete Python importable.
"""

# Versión del proyecto
__version__ = "1.0.0"

# Importaciones principales para facilitar el uso
from .pdf_processor import PDFProcessor
from .question_generator import QuestionGenerator
from .memory_optimizer import memory_optimizer
from .gui import PDFQuestionGUI, run_gui

__all__ = [
    'PDFProcessor',
    'QuestionGenerator', 
    'memory_optimizer',
    'PDFQuestionGUI',
    'run_gui'
]
