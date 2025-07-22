"""
Procesador de PDF optimizado para streaming y bajo uso de memoria.
Extrae texto de documentos PDF en chunks para minimizar el uso de RAM.
"""
import fitz  # PyMuPDF
import logging
from typing import List, Iterator, Optional, Dict
import re
from pathlib import Path
from .memory_optimizer import memory_optimizer

class PDFProcessor:
    def get_full_text(self, pdf_path: str) -> str:
        """
        Devuelve el texto completo del PDF (útil para exámenes).
        """
        return self.extract_text_from_pdf(pdf_path)
    """Procesador de PDF con optimización de memoria."""
    
    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        """
        Inicializa el procesador de PDF.
        
        Args:
            chunk_size: Tamaño de cada chunk en tokens aproximados
            overlap: Solapamiento entre chunks para mantener contexto
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.logger = logging.getLogger(__name__)
    
    @memory_optimizer.monitor_memory_usage("extract_text_from_pdf")
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extrae texto completo del PDF.
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            Texto extraído del PDF
            
        Raises:
            FileNotFoundError: Si el archivo no existe
            Exception: Si hay error al procesar el PDF
        """
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"El archivo {pdf_path} no existe")
        
        try:
            text_content = []
            
            # Abrir PDF
            with fitz.open(pdf_path) as doc:
                self.logger.info(f"Procesando PDF: {Path(pdf_path).name} ({len(doc)} páginas)")
                
                for page_num, page in enumerate(doc, 1):
                    # Extraer texto de la página
                    page_text = page.get_text()
                    
                    if page_text.strip():
                        # Limpiar texto
                        cleaned_text = self._clean_text(page_text)
                        text_content.append(cleaned_text)
                    
                    # Limpieza de memoria cada 10 páginas
                    if page_num % 10 == 0:
                        memory_optimizer.cleanup_memory()
                    
                    self.logger.debug(f"Procesada página {page_num}/{len(doc)}")
            
            full_text = "\n\n".join(text_content)
            self.logger.info(f"Texto extraído: {len(full_text)} caracteres")
            
            return full_text
            
        except Exception as e:
            self.logger.error(f"Error al extraer texto del PDF: {str(e)}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """
        Limpia y normaliza el texto extraído.
        
        Args:
            text: Texto crudo extraído del PDF
            
        Returns:
            Texto limpio y normalizado
        """
        # Eliminar caracteres de control
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', text)
        
        # Normalizar espacios en blanco
        text = re.sub(r'\s+', ' ', text)
        
        # Eliminar líneas muy cortas (probablemente headers/footers)
        lines = text.split('\n')
        filtered_lines = []
        
        for line in lines:
            line = line.strip()
            if len(line) > 10:  # Solo líneas con más de 10 caracteres
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    @memory_optimizer.monitor_memory_usage("create_text_chunks")
    def create_text_chunks(self, text: str) -> Iterator[str]:
        """
        Divide el texto en chunks con solapamiento.
        
        Args:
            text: Texto completo a dividir
            
        Yields:
            Chunks de texto con solapamiento
        """
        # Obtener tamaño óptimo de chunk basado en memoria disponible
        optimal_chunk_size = memory_optimizer.get_optimal_chunk_size(
            len(text), self.chunk_size
        )
        
        words = text.split()
        total_words = len(words)
        
        self.logger.info(f"Dividiendo texto en chunks (tamaño: {optimal_chunk_size}, total palabras: {total_words})")
        
        start_idx = 0
        chunk_count = 0
        
        while start_idx < total_words:
            # Calcular fin del chunk
            end_idx = min(start_idx + optimal_chunk_size, total_words)
            
            # Extraer chunk
            chunk_words = words[start_idx:end_idx]
            chunk_text = ' '.join(chunk_words)
            
            # Solo devolver chunks con contenido significativo
            if len(chunk_text.strip()) > 50:
                chunk_count += 1
                self.logger.debug(f"Generado chunk {chunk_count}: {len(chunk_text)} caracteres")
                yield chunk_text
            
            # Avanzar con solapamiento
            if end_idx >= total_words:
                break
            
            start_idx = end_idx - self.overlap
        
        self.logger.info(f"Generados {chunk_count} chunks de texto")
    
    def get_pdf_metadata(self, pdf_path: str) -> Dict[str, str]:
        """
        Extrae metadatos del PDF.
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            Diccionario con metadatos del PDF
        """
        try:
            with fitz.open(pdf_path) as doc:
                metadata = doc.metadata
                
                return {
                    'title': metadata.get('title', 'Sin título'),
                    'author': metadata.get('author', 'Autor desconocido'),
                    'subject': metadata.get('subject', ''),
                    'pages': len(doc),
                    'file_size_mb': Path(pdf_path).stat().st_size / (1024 * 1024)
                }
        except Exception as e:
            self.logger.error(f"Error al obtener metadatos: {str(e)}")
            return {}
    
    @memory_optimizer.monitor_memory_usage("process_pdf_streaming")
    def process_pdf_streaming(self, pdf_path: str) -> Iterator[Dict[str, str]]:
        """
        Procesa PDF en modo streaming para minimizar memoria.
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Yields:
            Diccionarios con chunk de texto y metadatos
        """
        # Extraer metadatos
        metadata = self.get_pdf_metadata(pdf_path)
        
        # Extraer texto
        full_text = self.extract_text_from_pdf(pdf_path)
        
        # Generar chunks
        for i, chunk in enumerate(self.create_text_chunks(full_text)):
            yield {
                'chunk_id': i,
                'text': chunk,
                'metadata': metadata,
                'chunk_length': len(chunk)
            }
            
            # Limpieza periódica de memoria
            if i % 5 == 0:
                memory_optimizer.cleanup_memory()
    
    def validate_pdf(self, pdf_path: str) -> bool:
        """
        Valida que el archivo PDF sea procesable.
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            True si el PDF es válido
        """
        try:
            path = Path(pdf_path)
            
            # Verificar que existe
            if not path.exists():
                self.logger.error(f"Archivo no encontrado: {pdf_path}")
                return False
            
            # Verificar extensión
            if path.suffix.lower() != '.pdf':
                self.logger.error(f"No es un archivo PDF: {pdf_path}")
                return False
            
            # Verificar que se puede abrir
            with fitz.open(pdf_path) as doc:
                if len(doc) == 0:
                    self.logger.error(f"PDF vacío: {pdf_path}")
                    return False
                
                # Verificar que tiene texto
                first_page = doc[0]
                if not first_page.get_text().strip():
                    self.logger.warning(f"PDF puede ser solo imágenes: {pdf_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al validar PDF: {str(e)}")
            return False
