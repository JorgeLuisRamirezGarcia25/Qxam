#!/usr/bin/env python3
"""
PDF Question Generator - Generador de preguntas automático desde PDFs
Optimizado para funcionar con solo 4GB de RAM usando modelos ligeros de IA.

Uso:
    python main.py                                    # Interfaz gráfica
    python main.py --file documento.pdf             # Línea de comandos
    python main.py --help                           # Mostrar ayuda
"""

import argparse
import sys
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional

# Añadir el directorio src al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src import PDFProcessor, QuestionGenerator, memory_optimizer, run_gui

def setup_logging(verbose: bool = False):
    """
    Configura el sistema de logging.
    
    Args:
        verbose: Si True, muestra logs detallados
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def print_supported_models():
    """Muestra información de los modelos soportados."""
    models = QuestionGenerator.list_supported_models()
    
    print("\n🤖 MODELOS SOPORTADOS:")
    print("-" * 60)
    
    for model_name, config in models.items():
        print(f"📦 {model_name}")
        print(f"   Tamaño: {config['size_mb']}MB")
        print(f"   Descripción: {config['description']}")
        print(f"   Tipo: {config['type']}")
        print()

def print_memory_info():
    """Muestra información del uso de memoria."""
    memory_info = memory_optimizer.get_memory_usage()
    
    print("💾 INFORMACIÓN DE MEMORIA:")
    print("-" * 40)
    print(f"Proceso actual: {memory_info['process_memory_mb']:.1f} MB")
    print(f"Sistema usado: {memory_info['system_memory_percent']:.1f}%")
    print(f"Disponible: {memory_info['system_available_mb']:.0f} MB")
    print(f"Total: {memory_info['system_total_mb']:.0f} MB")
    print()

def save_questions_to_file(questions: List[Dict], output_path: str, pdf_path: str = None):
    """
    Guarda las preguntas en un archivo.
    
    Args:
        questions: Lista de preguntas generadas
        output_path: Ruta del archivo de salida
        pdf_path: Ruta del PDF original (opcional)
    """
    output_path = Path(output_path)
    
    try:
        if output_path.suffix.lower() == '.pdf':
            save_questions_to_pdf(questions, output_path, pdf_path)
        else:
            save_questions_to_text(questions, output_path, pdf_path)
        
        print(f"✅ Preguntas guardadas en: {output_path}")
        
    except Exception as e:
        print(f"❌ Error al guardar preguntas: {str(e)}")
        sys.exit(1)

def save_questions_to_text(questions: List[Dict], output_path: Path, pdf_path: str = None):
    """Guarda preguntas en archivo de texto."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("🤖 PREGUNTAS GENERADAS AUTOMÁTICAMENTE\\n")
        f.write("=" * 50 + "\\n\\n")
        
        if pdf_path:
            f.write(f"📄 Fuente: {Path(pdf_path).name}\\n")
            f.write(f"📊 Total de preguntas: {len(questions)}\\n\\n")
        
        for i, question_data in enumerate(questions, 1):
            f.write(f"{i:2d}. {question_data['question']}\\n")
            f.write(f"    🏷️  Tipo: {question_data.get('type', 'N/A')}\\n")
            f.write(f"    🤖 Modelo: {question_data.get('model', 'N/A')}\\n")
            f.write(f"    📏 Longitud fuente: {question_data.get('source_length', 'N/A')} caracteres\\n\\n")

def save_questions_to_pdf(questions: List[Dict], output_path: Path, pdf_path: str = None):
    """Guarda preguntas en archivo PDF."""
    try:
        from fpdf import FPDF
    except ImportError:
        print("❌ Error: fpdf2 no está instalado. Instálalo con: pip install fpdf2")
        sys.exit(1)
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    # Título
    pdf.cell(0, 10, "PREGUNTAS GENERADAS AUTOMATICAMENTE", ln=True, align="C")
    pdf.ln(10)
    
    # Información del archivo fuente
    if pdf_path:
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 10, f"Fuente: {Path(pdf_path).name}", ln=True)
        pdf.cell(0, 10, f"Total de preguntas: {len(questions)}", ln=True)
        pdf.ln(5)
    
    # Preguntas
    pdf.set_font("Arial", size=12)
    
    for i, question_data in enumerate(questions, 1):
        # Pregunta
        question_text = f"{i:2d}. {question_data['question']}"
        # Codificar para PDF (manejar caracteres especiales)
        try:
            pdf.multi_cell(0, 10, question_text)
        except UnicodeEncodeError:
            # Fallback para caracteres especiales
            safe_text = question_text.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 10, safe_text)
        
        # Información adicional
        pdf.set_font("Arial", "I", 10)
        info_text = f"Tipo: {question_data.get('type', 'N/A')} | Modelo: {question_data.get('model', 'N/A')}"
        pdf.cell(0, 5, info_text, ln=True)
        pdf.ln(5)
        
        pdf.set_font("Arial", size=12)
    
    pdf.output(str(output_path))

def generate_questions_cli(args):
    """
    Genera preguntas usando la interfaz de línea de comandos.
    
    Args:
        args: Argumentos parseados de argparse
    """
    pdf_path = args.file
    model_name = args.model
    num_questions = args.num_questions
    max_length = args.max_length
    output_path = args.output
    
    # Validar archivo PDF
    if not Path(pdf_path).exists():
        print(f"❌ Error: El archivo {pdf_path} no existe")
        sys.exit(1)
    
    # Crear procesador de PDF
    print("📄 Inicializando procesador de PDF...")
    pdf_processor = PDFProcessor()
    
    if not pdf_processor.validate_pdf(pdf_path):
        print(f"❌ Error: El archivo {pdf_path} no es un PDF válido")
        sys.exit(1)
    
    # Mostrar información del PDF
    metadata = pdf_processor.get_pdf_metadata(pdf_path)
    print(f"📋 PDF: {metadata.get('title', Path(pdf_path).name)}")
    print(f"📄 Páginas: {metadata.get('pages', 'N/A')}")
    print(f"💾 Tamaño: {metadata.get('file_size_mb', 0):.1f}MB")
    print()
    
    # Crear generador de preguntas
    print(f"🤖 Cargando modelo {model_name}...")
    question_generator = QuestionGenerator(
        model_name=model_name,
        max_length=max_length
    )
    
    if not question_generator.load_model():
        print(f"❌ Error: No se pudo cargar el modelo {model_name}")
        sys.exit(1)
    
    model_info = question_generator.get_model_info()
    print(f"✅ Modelo cargado: {model_info['description']}")
    print()
    
    # Procesar PDF y generar preguntas
    print("🔄 Procesando PDF y generando preguntas...")
    all_questions = []
    
    try:
        chunk_count = 0
        
        for chunk_data in pdf_processor.process_pdf_streaming(pdf_path):
            chunk_count += 1
            chunk_text = chunk_data['text']
            
            print(f"📝 Procesando chunk {chunk_count} ({len(chunk_text)} caracteres)...")
            
            # Calcular preguntas por chunk
            questions_per_chunk = min(3, max(1, num_questions // 5))
            
            chunk_questions = question_generator.generate_questions_from_text(
                chunk_text,
                num_questions=questions_per_chunk
            )
            
            if chunk_questions:
                all_questions.extend(chunk_questions)
                print(f"✅ Generadas {len(chunk_questions)} preguntas del chunk {chunk_count}")
            
            # Limitar número total
            if len(all_questions) >= num_questions:
                all_questions = all_questions[:num_questions]
                break
        
        # Mostrar resultados
        print(f"\\n🎉 GENERACIÓN COMPLETADA")
        print(f"📊 Total de preguntas válidas: {len(all_questions)}")
        print("-" * 50)
        
        # Mostrar preguntas
        for i, question_data in enumerate(all_questions, 1):
            print(f"{i:2d}. {question_data['question']}")
            print(f"    🏷️  {question_data.get('type', 'N/A')} | 🤖 {question_data.get('model', 'N/A')}")
            print()
        
        # Guardar si se especificó archivo de salida
        if output_path:
            save_questions_to_file(all_questions, output_path, pdf_path)
        elif len(all_questions) > 0:
            # Preguntar si quiere guardar
            try:
                response = input("💾 ¿Deseas guardar las preguntas en un archivo? (s/N): ").strip().lower()
                if response in ['s', 'si', 'sí', 'y', 'yes']:
                    default_name = f"preguntas_{Path(pdf_path).stem}.txt"
                    output_file = input(f"📝 Nombre del archivo [{default_name}]: ").strip()
                    
                    if not output_file:
                        output_file = default_name
                    
                    # Crear directorio output si no existe
                    output_dir = Path("output")
                    output_dir.mkdir(exist_ok=True)
                    
                    output_path = output_dir / output_file
                    save_questions_to_file(all_questions, str(output_path), pdf_path)
            
            except KeyboardInterrupt:
                print("\\n👋 Proceso interrumpido por el usuario")
        
    except Exception as e:
        print(f"❌ Error durante la generación: {str(e)}")
        sys.exit(1)
    
    finally:
        # Limpiar recursos
        print("🧹 Limpiando recursos...")
        question_generator.unload_model()
        memory_optimizer.cleanup_memory(force=True)

def main():
    """Función principal del programa."""
    parser = argparse.ArgumentParser(
        description="PDF Question Generator - Generador de preguntas optimizado para 4GB RAM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python main.py                                    # Abrir interfaz gráfica
  python main.py --file documento.pdf             # Procesar PDF específico
  python main.py --file doc.pdf --model t5-small  # Usar modelo específico
  python main.py --file doc.pdf --output preguntas.txt  # Especificar archivo de salida
  python main.py --models                          # Mostrar modelos disponibles
  python main.py --memory-info                     # Mostrar información de memoria

Modelos disponibles:
  - distilgpt2: 300MB, rápido y eficiente (por defecto)
  - t5-small: 200MB, ideal para generación de preguntas  
  - albert-base-v2: 40MB, muy ligero pero con capacidades limitadas
        """
    )
    
    # Argumentos principales
    parser.add_argument(
        '--file', '-f',
        type=str,
        help='Archivo PDF a procesar'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Archivo de salida para las preguntas (txt o pdf)'
    )
    
    parser.add_argument(
        '--model', '-m',
        type=str,
        default='distilgpt2',
        choices=list(QuestionGenerator.SUPPORTED_MODELS.keys()),
        help='Modelo de IA a usar (por defecto: distilgpt2)'
    )
    
    parser.add_argument(
        '--num-questions', '-n',
        type=int,
        default=10,
        help='Número de preguntas a generar (por defecto: 10)'
    )
    
    parser.add_argument(
        '--max-length',
        type=int,
        default=100,
        help='Longitud máxima de cada pregunta en tokens (por defecto: 100)'
    )
    
    # Argumentos de información
    parser.add_argument(
        '--models',
        action='store_true',
        help='Mostrar información de modelos disponibles'
    )
    
    parser.add_argument(
        '--memory-info',
        action='store_true',
        help='Mostrar información del uso de memoria'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mostrar información detallada'
    )
    
    # Parsear argumentos
    args = parser.parse_args()
    
    # Configurar logging
    setup_logging(args.verbose)
    
    # Mostrar información y salir
    if args.models:
        print_supported_models()
        return
    
    if args.memory_info:
        print_memory_info()
        return
    
    # Determinar modo de operación
    if args.file:
        # Modo línea de comandos
        generate_questions_cli(args)
    else:
        # Modo GUI
        print("🚀 Iniciando interfaz gráfica...")
        print("💡 Tip: Usa --help para ver opciones de línea de comandos")
        print()
        
        try:
            run_gui()
        except KeyboardInterrupt:
            print("\\n👋 Aplicación cerrada por el usuario")
        except Exception as e:
            print(f"❌ Error en la aplicación: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    main()
