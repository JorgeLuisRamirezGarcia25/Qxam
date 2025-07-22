"""
Generador de preguntas usando modelos de IA ligeros optimizados para 4GB RAM.
Soporta distilgpt2, t5-small, y albert-base-v2.
"""
import torch
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM,
    T5Tokenizer, T5ForConditionalGeneration,
    pipeline, set_seed
)
from typing import List, Dict, Optional, Union
import logging
import re
from .memory_optimizer import memory_optimizer

class QuestionGenerator:
    def present_multiple_choice_exam(self, exam: list) -> list:
        """
        Presenta el examen de opción múltiple por consola y recolecta las respuestas del usuario.
        Args:
            exam: lista de preguntas (cada una con 'question', 'options', 'answer')
        Returns:
            Lista de respuestas seleccionadas por el usuario (mismo orden)
        """
        user_answers = []
        for idx, q in enumerate(exam, 1):
            print(f"\nPregunta {idx}: {q['question']}")
            for i, opt in enumerate(q['options']):
                print(f"  {chr(65+i)}) {opt}")
            while True:
                ans = input(f"Selecciona una opción (A-{chr(65+len(q['options'])-1)}): ").strip().upper()
                if ans and ans in [chr(65+i) for i in range(len(q['options']))]:
                    user_answers.append(q['options'][ord(ans)-65])
                    break
                else:
                    print("Opción inválida. Intenta de nuevo.")
        return user_answers
    def save_exam_results(self, grade_result: dict, filename: str = "resultados_examen.txt"):
        """
        Guarda los resultados del examen en un archivo de texto.
        Args:
            grade_result: dict devuelto por grade_multiple_choice_exam
            filename: nombre del archivo a guardar
        """
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Resultados del examen\n")
            f.write(f"Aciertos: {grade_result['correct']} de {grade_result['total']}\n")
            f.write(f"Porcentaje: {grade_result['score']:.2f}%\n\n")
            for idx, det in enumerate(grade_result['details'], 1):
                f.write(f"Pregunta {idx}: {det['question']}\n")
                f.write(f"  Seleccionada: {det['selected']}\n")
                f.write(f"  Correcta: {det['correct_answer']}\n")
                f.write(f"  {'✔️ Correcto' if det['is_correct'] else '❌ Incorrecto'}\n\n")
    def grade_multiple_choice_exam(self, exam: list, user_answers: list) -> dict:
        """
        Califica un examen de opción múltiple y retorna el porcentaje de aciertos y detalles.
        Args:
            exam: lista de preguntas (cada una con 'question', 'options', 'answer')
            user_answers: lista de respuestas seleccionadas por el usuario (mismo orden)
        Returns:
            dict con 'score' (porcentaje), 'correct' (número de aciertos), 'total', y detalles por pregunta
        """
        correct = 0
        details = []
        for idx, (q, user_ans) in enumerate(zip(exam, user_answers)):
            is_correct = (user_ans == q['answer'])
            if is_correct:
                correct += 1
            details.append({
                'question': q['question'],
                'selected': user_ans,
                'correct_answer': q['answer'],
                'is_correct': is_correct
            })
        total = len(exam)
        score = (correct / total * 100) if total > 0 else 0
        return {
            'score': score,
            'correct': correct,
            'total': total,
            'details': details
        }
    def generate_multiple_choice_exam(self, text: str, num_questions: int = 5, num_options: int = 4) -> list:
        """
        Genera un examen de opción múltiple a partir de un texto, usando chunks pequeños para no saturar la memoria.
        Cada pregunta tiene una respuesta correcta (la generada) y opciones distractoras generadas automáticamente.
        """
        # Importar aquí para evitar dependencias circulares
        from .pdf_processor import PDFProcessor
        pdf_processor = PDFProcessor()
        # Dividir el texto en chunks
        chunks = list(pdf_processor.create_text_chunks(text))
        exam = []
        used_questions = set()
        chunk_idx = 0
        # Generar una pregunta por chunk hasta alcanzar el número deseado
        while len(exam) < num_questions and chunk_idx < len(chunks):
            chunk_text = chunks[chunk_idx]
            questions = self.generate_questions_from_text(chunk_text, num_questions=1)
            for q in questions:
                question_text = q['question']
                if question_text in used_questions:
                    continue
                correct_answer = self._extract_answer_from_question(question_text, chunk_text)
                distractors = self._generate_distractors(correct_answer, chunk_text, num_options - 1)
                options = distractors + [correct_answer]
                import random
                random.shuffle(options)
                exam.append({
                    'question': question_text,
                    'options': options,
                    'answer': correct_answer
                })
                used_questions.add(question_text)
                if len(exam) >= num_questions:
                    break
            chunk_idx += 1
        return exam

    def _extract_answer_from_question(self, question: str, context: str) -> str:
        """
        Extrae una posible respuesta del contexto para la pregunta (simple: devuelve la frase más similar).
        """
        import difflib
        sentences = [s.strip() for s in context.split('.') if len(s.strip()) > 10]
        best = difflib.get_close_matches(question, sentences, n=1)
        return best[0] if best else sentences[0] if sentences else "Respuesta no disponible"

    def _generate_distractors(self, correct: str, context: str, n: int) -> list:
        """
        Genera opciones distractoras simples a partir del contexto.
        """
        import random
        sentences = [s.strip() for s in context.split('.') if len(s.strip()) > 10 and s.strip() != correct]
        distractors = random.sample(sentences, min(n, len(sentences))) if sentences else ["Opción incorrecta"] * n
        return distractors
    """Generador de preguntas con modelos ligeros de IA."""
    
    SUPPORTED_MODELS = {
        'iarfmoose/t5-base-question-generator': {
            'type': 'qg',
            'size_mb': 250,
            'description': 'T5-base entrenado para generación de preguntas (QG) en inglés',
        },
        't5-small': {
            'type': 'qg',
            'size_mb': 200,
            'description': 'T5-small para generación de preguntas (menos preciso)',
        },
        'mrm8488/t5-base-finetuned-question-generation-ap': {
            'type': 'qg',
            'size_mb': 250,
            'description': 'T5-base afinado para generación de preguntas en español',
        }
    }
    # ...existing code...

    def __init__(self, model_name: str = None, max_length: int = 100, device: str = 'cpu'):
        # Forzar modelo español por defecto si no se especifica
        if model_name is None or model_name not in self.SUPPORTED_MODELS:
            self.model_name = 'mrm8488/t5-base-finetuned-question-generation-ap'
        else:
            self.model_name = model_name
        self.max_length = max_length
        self.device = device if torch.cuda.is_available() else 'cpu'
        self.pipeline = None
        self.logger = logging.getLogger(__name__)

    @memory_optimizer.monitor_memory_usage("load_model")
    def load_model(self) -> bool:
        try:
            self.logger.info(f"Cargando modelo {self.model_name}...")
            self.pipeline = pipeline(
                "text2text-generation",
                model=self.model_name,
                tokenizer=self.model_name,
                device=0 if self.device == 'cuda' else -1
            )
            self.logger.info(f"Modelo {self.model_name} cargado exitosamente")
            return True
        except Exception as e:
            self.logger.error(f"Error al cargar modelo {self.model_name}: {str(e)}")
            return False

    @memory_optimizer.monitor_memory_usage("generate_questions_from_text")
    def generate_questions_from_text(self, text: str, num_questions: int = 5) -> List[Dict[str, str]]:
        """
        Genera preguntas a partir de un texto usando un modelo T5 QG.
        El modelo espera prompts del tipo: 'generate question: <context> answer: <answer>'
        """
        if not self.pipeline:
            if not self.load_model():
                raise RuntimeError("No se pudo cargar el modelo")

        # Extraer frases del texto como respuestas candidatas
        import re
        # Usar frases más largas y variadas como contexto
        sentences = re.split(r'(?<=[.!?])\s+', text)
        questions = []
        used = set()
        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 30:
                continue
            if len(questions) >= num_questions:
                break
            # Prompt y validación según modelo
            if self.model_name.startswith('mrm8488'):
                prompt = f"contexto: {sent} respuesta: {sent}"
                lang = 'es'
            else:
                prompt = f"generate question: {sent} answer: {sent}"
                lang = 'en'
            try:
                if self.pipeline is None:
                    self.logger.error("Pipeline no inicializado")
                    continue
                result = self.pipeline(
                    prompt,
                    num_return_sequences=3,
                    clean_up_tokenization_spaces=True
                )
                for r in result:
                    question = r['generated_text'].strip()
                    # Validación para inglés
                    if lang == 'en':
                        if (question and question not in used and len(question) > 10 and len(question) < 200
                            and '?' in question
                            and question[0].isupper()
                            and not any(c in question for c in '¿¡')
                            and not question.lower().startswith('context:')
                            and not question.lower().startswith('answer:')):
                            questions.append({
                                'question': question,
                                'type': 'QG',
                                'model': self.model_name
                            })
                            used.add(question)
                    # Validación para español
                    else:
                        if (question and question not in used and len(question) > 10 and len(question) < 200
                            and ('¿' in question or '?' in question)
                            and not question.lower().startswith('what')
                            and not question.lower().startswith('who')
                            and not question.lower().startswith('when')
                            and not question.lower().startswith('where')
                            and not question.lower().startswith('why')
                            and not question.lower().startswith('how')):
                            questions.append({
                                'question': question,
                                'type': 'QG',
                                'model': self.model_name
                            })
                            used.add(question)
            except Exception as e:
                self.logger.warning(f"Error generando pregunta: {e}")
        self.logger.info(f"Generadas {len(questions)} preguntas válidas")
        return questions

    def unload_model(self):
        """Libera el modelo de memoria."""
        self.pipeline = None
        memory_optimizer.cleanup_memory(force=True)

    def get_model_info(self) -> Dict[str, str]:
        config = self.SUPPORTED_MODELS.get(self.model_name, {})
        return {
            'name': self.model_name,
            'type': config.get('type', ''),
            'size_mb': str(config.get('size_mb', '')),
            'description': config.get('description', '')
        }
    # ...existing code...
