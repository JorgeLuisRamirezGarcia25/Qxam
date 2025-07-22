"""
Interfaz gráfica para el generador de preguntas PDF.
Diseñada para ser simple y eficiente en sistemas con 4GB RAM.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import threading
import logging
from typing import List, Dict, Optional
import os

from .pdf_processor import PDFProcessor
from .question_generator import QuestionGenerator
from .memory_optimizer import memory_optimizer

class PDFQuestionGUI:
    def create_exam_widgets(self, parent):
        """Crea widgets para el examen de opción múltiple en el contenedor dado."""
        self.exam_frame = ttk.LabelFrame(parent, text="Examen de opción múltiple", padding="10")
        self.exam_question_label = ttk.Label(self.exam_frame, text="", font=("Arial", 12, "bold"), wraplength=700, justify="left")
        self.exam_options_vars = []
        self.exam_options_rbs = []
        self.exam_next_button = ttk.Button(self.exam_frame, text="Siguiente", command=self.next_exam_question)
        self.exam_submit_button = ttk.Button(self.exam_frame, text="Finalizar examen", command=self.finish_exam)
        self.exam_result_label = ttk.Label(self.exam_frame, text="", font=("Arial", 11, "bold"), foreground="blue")

    def show_exam(self):
        """Inicia el examen de opción múltiple en una ventana modal."""
        if not self.generated_questions:
            messagebox.showwarning("Advertencia", "Primero genera preguntas para crear el examen.")
            return
        if not self.question_generator:
            messagebox.showerror("Error", "No hay generador de preguntas disponible.")
            return
        if not self.current_pdf_path:
            messagebox.showerror("Error", "No hay PDF cargado.")
            return
        # Generar examen
        self.exam = self.question_generator.generate_multiple_choice_exam(
            self.pdf_processor.get_full_text(self.current_pdf_path),
            num_questions=len(self.generated_questions),
            num_options=4
        )
        self.user_exam_answers = []
        self.current_exam_index = 0
        # Crear ventana modal
        self.exam_window = tk.Toplevel(self.root)
        self.exam_window.title("Examen de opción múltiple")
        self.exam_window.geometry("800x400")
        self.exam_window.transient(self.root)
        self.exam_window.grab_set()
        self.create_exam_widgets(self.exam_window)
        self.exam_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.display_exam_question()

    def display_exam_question(self):
        """Muestra la pregunta actual del examen y sus opciones en la ventana modal."""
        for rb in self.exam_options_rbs:
            rb.destroy()
        self.exam_options_vars.clear()
        self.exam_options_rbs.clear()
        q = self.exam[self.current_exam_index]
        self.exam_question_label.config(text=f"{self.current_exam_index+1}. {q['question']}")
        self.exam_question_label.pack(anchor="w", pady=(0, 5))
        var = tk.StringVar()
        for opt in q['options']:
            rb = ttk.Radiobutton(self.exam_frame, text=opt, variable=var, value=opt)
            rb.pack(anchor="w", padx=10)
            self.exam_options_rbs.append(rb)
        self.exam_options_vars.append(var)
        # Botones
        if self.current_exam_index < len(self.exam) - 1:
            self.exam_next_button.pack(anchor="e", pady=(10, 0))
            self.exam_submit_button.pack_forget()
        else:
            self.exam_next_button.pack_forget()
            self.exam_submit_button.pack(anchor="e", pady=(10, 0))

    def next_exam_question(self):
        """Guarda respuesta y muestra la siguiente pregunta."""
        var = self.exam_options_vars[-1]
        answer = var.get()
        if not answer:
            messagebox.showwarning("Advertencia", "Selecciona una opción antes de continuar.")
            return
        self.user_exam_answers.append(answer)
        self.current_exam_index += 1
        self.display_exam_question()

    def finish_exam(self):
        """Finaliza el examen, califica y muestra el resultado en la ventana modal."""
        var = self.exam_options_vars[-1]
        answer = var.get()
        if not answer:
            messagebox.showwarning("Advertencia", "Selecciona una opción antes de finalizar.")
            return
        self.user_exam_answers.append(answer)
        if not self.question_generator:
            messagebox.showerror("Error", "No hay generador de preguntas disponible.")
            return
        result = self.question_generator.grade_multiple_choice_exam(self.exam, self.user_exam_answers)
        self.exam_result_label.config(text=f"Aciertos: {result['correct']} de {result['total']}  |  Porcentaje: {result['score']:.2f}%")
        self.exam_result_label.pack(anchor="w", pady=(10, 0))
        self.exam_next_button.pack_forget()
        self.exam_submit_button.pack_forget()
        # Cerrar ventana modal tras mostrar resultado (opcional: dejar unos segundos o botón de cerrar)
        close_btn = ttk.Button(self.exam_frame, text="Cerrar", command=self.exam_window.destroy)
        close_btn.pack(anchor="e", pady=(10, 0))
    """Interfaz gráfica principal."""
    
    def __init__(self, root):
        """
        Inicializa la interfaz gráfica.
        
        Args:
            root: Ventana raíz de Tkinter
        """
        self.root = root
        self.root.title("PDF Question Generator (4GB RAM Optimized)")
        self.root.geometry("900x700")
        
        # Variables
        self.pdf_processor = PDFProcessor()
        self.question_generator = None
        self.current_pdf_path = None
        self.generated_questions = []
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Crear interfaz
        self.create_widgets()
        self.setup_layout()
        
        # Variables de estado
        self.processing = False
    
    def create_widgets(self):
        """Crea todos los widgets de la interfaz."""
        
        # Frame principal
        self.main_frame = ttk.Frame(self.root, padding="10")
        
        # Título
        self.title_label = ttk.Label(
            self.main_frame,
            text="PDF Question Generator",
            font=("Arial", 16, "bold")
        )
        
        # Subtítulo con información de memoria
        self.subtitle_label = ttk.Label(
            self.main_frame,
            text="Optimizado para 4GB RAM - Modelos ligeros de IA",
            font=("Arial", 10)
        )
        
        # Frame de selección de archivo
        self.file_frame = ttk.LabelFrame(self.main_frame, text="Selección de PDF", padding="10")
        
        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(
            self.file_frame,
            textvariable=self.file_path_var,
            state="readonly",
            width=50
        )
        
        self.browse_button = ttk.Button(
            self.file_frame,
            text="Seleccionar PDF",
            command=self.browse_file
        )
        
        # Frame de configuración
        self.config_frame = ttk.LabelFrame(self.main_frame, text="Configuración", padding="10")
        
        # Selección de modelo
        ttk.Label(self.config_frame, text="Modelo de IA:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.model_var = tk.StringVar(value="iarfmoose/t5-base-question-generator")
        self.model_combo = ttk.Combobox(
            self.config_frame,
            textvariable=self.model_var,
            values=list(QuestionGenerator.SUPPORTED_MODELS.keys()),
            state="readonly",
            width=20
        )
        self.model_combo.bind("<<ComboboxSelected>>", self.on_model_changed)
        
        # Número de preguntas
        ttk.Label(self.config_frame, text="Número de preguntas:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.num_questions_var = tk.StringVar(value="10")
        self.num_questions_spin = ttk.Spinbox(
            self.config_frame,
            from_=1,
            to=50,
            textvariable=self.num_questions_var,
            width=10
        )
        # Longitud máxima
        ttk.Label(self.config_frame, text="Longitud máxima:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.max_length_var = tk.StringVar(value="100")
        self.max_length_spin = ttk.Spinbox(
            self.config_frame,
            from_=50,
            to=200,
            textvariable=self.max_length_var,
            width=10
        )
        # Información del modelo
        self.model_info_label = ttk.Label(
            self.config_frame,
            text="",
            font=("Arial", 9),
            foreground="gray"
        )
        # Frame de acciones
        self.action_frame = ttk.Frame(self.main_frame)
        self.generate_button = ttk.Button(
            self.action_frame,
            text="Generar Preguntas",
            command=self.generate_questions,
            style="Accent.TButton"
        )
        self.save_button = ttk.Button(
            self.action_frame,
            text="Guardar Resultados",
            command=self.save_results,
            state="disabled"
        )
        # Botón para examen
        self.exam_button = ttk.Button(
            self.action_frame,
            text="Generar Examen",
            command=self.show_exam,
            state="disabled"
        )
        # Ya no se llama aquí, solo se llama con parent en show_exam
        # Barra de progreso
        self.progress_var = tk.StringVar(value="Listo")
        self.progress_label = ttk.Label(self.main_frame, textvariable=self.progress_var)
        self.progress_bar = ttk.Progressbar(
            self.main_frame,
            mode="indeterminate"
        )
        # Frame de resultados
        self.results_frame = ttk.LabelFrame(self.main_frame, text="Preguntas Generadas", padding="10")
        self.results_text = scrolledtext.ScrolledText(
            self.results_frame,
            wrap=tk.WORD,
            height=15,
            width=80
        )
        # Frame de información de memoria
        self.memory_frame = ttk.LabelFrame(self.main_frame, text="Uso de Memoria", padding="5")
        self.memory_info_label = ttk.Label(
            self.memory_frame,
            text="",
            font=("Arial", 9)
        )
        # Actualizar información inicial
        self.update_model_info()
        self.update_memory_info()
    
    def setup_layout(self):
        """Configura el layout de los widgets."""
        
        self.main_frame.pack(fill="both", expand=True)
        
        # Título
        self.title_label.pack(pady=(0, 5))
        self.subtitle_label.pack(pady=(0, 10))
        
        # Frame de archivo
        self.file_frame.pack(fill="x", pady=(0, 10))
        self.file_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.browse_button.pack(side="right")
        
        # Frame de configuración
        self.config_frame.pack(fill="x", pady=(0, 10))
        
        # Layout de configuración
        self.model_combo.grid(row=0, column=1, sticky="w", padx=(10, 5), pady=2)
        self.num_questions_spin.grid(row=1, column=1, sticky="w", padx=(10, 5), pady=2)
        self.max_length_spin.grid(row=2, column=1, sticky="w", padx=(10, 5), pady=2)
        self.model_info_label.grid(row=3, column=0, columnspan=2, sticky="w", padx=5, pady=(10, 0))
        
        # Frame de acciones
        self.action_frame.pack(fill="x", pady=(0, 10))
        self.generate_button.pack(side="left", padx=(0, 10))
        self.save_button.pack(side="left")
        self.exam_button.pack(side="left", padx=(10, 0))
        
        # Progreso
        self.progress_label.pack(pady=(0, 5))
        self.progress_bar.pack(fill="x", pady=(0, 10))
        
        # Resultados
        self.results_frame.pack(fill="both", expand=True, pady=(0, 10))
        self.results_text.pack(fill="both", expand=True)
        
        # Memoria
        self.memory_frame.pack(fill="x")
        self.memory_info_label.pack()
        
        # Timer para actualizar memoria
        self.root.after(5000, self.update_memory_info)
    
    def browse_file(self):
        """Abre diálogo para seleccionar archivo PDF."""
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if file_path:
            if self.pdf_processor.validate_pdf(file_path):
                self.current_pdf_path = file_path
                self.file_path_var.set(file_path)
                
                # Mostrar información del PDF
                metadata = self.pdf_processor.get_pdf_metadata(file_path)
                info = f"PDF cargado: {metadata.get('pages', 'N/A')} páginas, {metadata.get('file_size_mb', 0):.1f}MB"
                self.progress_var.set(info)
            else:
                messagebox.showerror("Error", "El archivo PDF seleccionado no es válido")
    
    def on_model_changed(self, event=None):
        """Callback cuando cambia la selección del modelo."""
        self.update_model_info()
        
        # Descargar modelo anterior si existe
        if self.question_generator:
            self.question_generator.unload_model()
            self.question_generator = None
    
    def update_model_info(self):
        """Actualiza la información del modelo seleccionado."""
        model_name = self.model_var.get()
        if model_name in QuestionGenerator.SUPPORTED_MODELS:
            config = QuestionGenerator.SUPPORTED_MODELS[model_name]
            info_text = f"Tamaño: {config['size_mb']}MB - {config['description']}"
            self.model_info_label.config(text=info_text)
    
    def update_memory_info(self):
        """Actualiza la información de uso de memoria."""
        try:
            memory_info = memory_optimizer.get_memory_usage()
            info_text = (
                f"Proceso: {memory_info['process_memory_mb']:.1f}MB | "
                f"Sistema: {memory_info['system_memory_percent']:.1f}% | "
                f"Disponible: {memory_info['system_available_mb']:.0f}MB"
            )
            self.memory_info_label.config(text=info_text)
            
            # Programar siguiente actualización
            self.root.after(5000, self.update_memory_info)
            
        except Exception as e:
            self.logger.warning(f"Error al actualizar información de memoria: {e}")
    
    def generate_questions(self):
        """Genera preguntas del PDF seleccionado."""
        if not self.current_pdf_path:
            messagebox.showwarning("Advertencia", "Por favor selecciona un archivo PDF")
            return
        
        if self.processing:
            messagebox.showinfo("Información", "Ya se está procesando un archivo")
            return
        
        # Iniciar generación en hilo separado
        thread = threading.Thread(target=self._generate_questions_thread, daemon=True)
        thread.start()
    
    def _generate_questions_thread(self):
        """Hilo para generar preguntas sin bloquear la GUI."""
        try:
            self.processing = True
            self._update_ui_processing(True)
            
            # Obtener parámetros
            model_name = self.model_var.get()
            num_questions = int(self.num_questions_var.get())
            max_length = int(self.max_length_var.get())
            
            # Crear generador si no existe
            if not self.question_generator or self.question_generator.model_name != model_name:
                self.progress_var.set(f"Cargando modelo {model_name}...")
                
                if self.question_generator:
                    self.question_generator.unload_model()
                
                self.question_generator = QuestionGenerator(
                    model_name=model_name,
                    max_length=max_length
                )
                
                if not self.question_generator.load_model():
                    raise RuntimeError("Error al cargar el modelo")
            
            self.progress_var.set("Procesando PDF...")
            
            # Procesar PDF y generar preguntas
            all_questions = []
            
            if not self.current_pdf_path:
                raise RuntimeError("No hay PDF cargado.")
            for i, chunk_data in enumerate(self.pdf_processor.process_pdf_streaming(self.current_pdf_path)):
                self.progress_var.set(f"Procesando chunk {i+1}...")
                
                chunk_text = chunk_data['text']
                
                # Generar preguntas para este chunk
                questions_per_chunk = min(3, max(1, num_questions // 5))  # Distribuir preguntas
                
                chunk_questions = self.question_generator.generate_questions_from_text(
                    chunk_text,
                    num_questions=questions_per_chunk
                )
                
                all_questions.extend(chunk_questions)
                
                # Limitar número total de preguntas
                if len(all_questions) >= num_questions:
                    all_questions = all_questions[:num_questions]
                    break
            
            self.generated_questions = all_questions
            
            # Actualizar interfaz con resultados
            self.root.after(0, self._display_results)
            
        except Exception as e:
            self.logger.error(f"Error al generar preguntas: {str(e)}")
            error_msg = f"Error: {str(e)}"
            self.root.after(0, lambda: self._update_ui_error(error_msg))
        
        finally:
            self.processing = False
            self.root.after(0, lambda: self._update_ui_processing(False))
    
    def _update_ui_processing(self, is_processing: bool):
        """Actualiza la UI durante el procesamiento."""
        if is_processing:
            self.generate_button.config(state="disabled")
            self.progress_bar.start()
        else:
            self.generate_button.config(state="normal")
            self.progress_bar.stop()
            self.progress_var.set("Listo")
    
    def _update_ui_error(self, error_msg: str):
        """Actualiza la UI cuando hay error."""
        self.progress_var.set("Error")
        messagebox.showerror("Error", error_msg)
    
    def _display_results(self):
        """Muestra los resultados en la interfaz."""
        if not self.generated_questions:
            messagebox.showinfo("Información", "No se pudieron generar preguntas válidas")
            return
        
        # Limpiar área de resultados
        self.results_text.delete(1.0, tk.END)
        
        # Mostrar preguntas
        for i, question_data in enumerate(self.generated_questions, 1):
            question = question_data['question']
            question_type = question_data.get('type', 'Pregunta')
            model = question_data.get('model', 'N/A')
            
            result_text = f"{i:2d}. {question}\n"
            result_text += f"    Tipo: {question_type} | Modelo: {model}\n\n"
            
            self.results_text.insert(tk.END, result_text)
        
        # Habilitar botones de guardar y examen
        self.save_button.config(state="normal")
        self.exam_button.config(state="normal")
        
        # Actualizar estado
        self.progress_var.set(f"Generadas {len(self.generated_questions)} preguntas")
    
    def save_results(self):
        """Guarda los resultados en un archivo."""
        if not self.generated_questions:
            messagebox.showwarning("Advertencia", "No hay preguntas para guardar")
            return
        
        # Seleccionar archivo de destino
        file_path = filedialog.asksaveasfilename(
            title="Guardar preguntas",
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("PDF files", "*.pdf"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                if file_path.endswith('.pdf'):
                    self._save_to_pdf(file_path)
                else:
                    self._save_to_text(file_path)
                
                messagebox.showinfo("Éxito", f"Preguntas guardadas en {file_path}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {str(e)}")
    
    def _save_to_text(self, file_path: str):
        """Guarda las preguntas en un archivo de texto."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("PREGUNTAS GENERADAS AUTOMÁTICAMENTE\n")
            f.write("=" * 50 + "\n\n")
            
            if self.current_pdf_path:
                f.write(f"Fuente: {Path(self.current_pdf_path).name}\n")
                f.write(f"Total de preguntas: {len(self.generated_questions)}\n\n")
            
            for i, question_data in enumerate(self.generated_questions, 1):
                f.write(f"{i:2d}. {question_data['question']}\n")
                f.write(f"    Tipo: {question_data.get('type', 'N/A')}\n")
                f.write(f"    Modelo: {question_data.get('model', 'N/A')}\n\n")
    
    def _save_to_pdf(self, file_path: str):
        """Guarda las preguntas en un archivo PDF."""
        from fpdf import FPDF
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        
        # Título
        pdf.cell(0, 10, "PREGUNTAS GENERADAS AUTOMATICAMENTE", ln=True, align="C")
        pdf.ln(10)
        
        # Información del archivo fuente
        if self.current_pdf_path:
            pdf.set_font("Arial", size=10)
            pdf.cell(0, 10, f"Fuente: {Path(self.current_pdf_path).name}", ln=True)
            pdf.cell(0, 10, f"Total de preguntas: {len(self.generated_questions)}", ln=True)
            pdf.ln(5)
        
        # Preguntas
        pdf.set_font("Arial", size=12)
        
        for i, question_data in enumerate(self.generated_questions, 1):
            # Pregunta
            question_text = f"{i:2d}. {question_data['question']}"
            pdf.multi_cell(0, 10, question_text.encode('latin-1', 'replace').decode('latin-1'))
            
            # Información adicional
            pdf.set_font("Arial", "I", 10)
            info_text = f"Tipo: {question_data.get('type', 'N/A')} | Modelo: {question_data.get('model', 'N/A')}"
            pdf.cell(0, 5, info_text, ln=True)
            pdf.ln(5)
            
            pdf.set_font("Arial", size=12)
        
        pdf.output(file_path)


def run_gui():
    """Ejecuta la interfaz gráfica."""
    root = tk.Tk()
    
    # Configurar tema si está disponible
    try:
        style = ttk.Style()
        style.theme_use('clam')  # Tema más moderno
    except:
        pass
    
    # Crear aplicación
    app = PDFQuestionGUI(root)
    
    # Configurar cierre
    def on_closing():
        if app.question_generator:
            app.question_generator.unload_model()
        memory_optimizer.cleanup_memory(force=True)
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Ejecutar
    root.mainloop()


if __name__ == "__main__":
    run_gui()
