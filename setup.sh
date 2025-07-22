#!/bin/bash

# Script de configuración rápida para PDF Question Generator
# Optimizado para sistemas con 4GB de RAM

echo "🚀 Configurando PDF Question Generator..."

# Crear directorios necesarios
echo "📁 Creando directorios..."
mkdir -p models output

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado. Por favor instala Python 3.8 o superior."
    exit 1
fi

echo "✅ Python 3 encontrado: $(python3 --version)"

# Crear entorno virtual si no existe
if [ ! -d ".venv" ]; then
    echo "🔧 Creando entorno virtual..."
    python3 -m venv .venv
fi

# Activar entorno virtual
echo "🔌 Activando entorno virtual..."
source .venv/bin/activate

# Actualizar pip
echo "📦 Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias
echo "📥 Instalando dependencias optimizadas para 4GB RAM..."
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

# Configurar variables de entorno
echo "⚙️ Configurando variables de entorno..."
export TRANSFORMERS_CACHE="./models"
export TORCH_HOME="./models"
export TOKENIZERS_PARALLELISM="false"

# Verificar instalación
echo "🔍 Verificando instalación..."
python3 -c "import torch; import transformers; import fitz; print('✅ Todas las dependencias instaladas correctamente')"

# Descargar modelo por defecto (opcional)
read -p "¿Deseas descargar el modelo por defecto (distilgpt2 - 300MB)? (s/N): " response
if [[ "$response" =~ ^([sS][íi]?|[yY])$ ]]; then
    echo "📥 Descargando modelo distilgpt2..."
    python3 -c "
from transformers import AutoTokenizer, AutoModel
print('Descargando tokenizer...')
AutoTokenizer.from_pretrained('distilgpt2', cache_dir='./models')
print('Descargando modelo...')
AutoModel.from_pretrained('distilgpt2', cache_dir='./models')
print('✅ Modelo descargado')
"
fi

echo ""
echo "🎉 ¡Configuración completada!"
echo ""
echo "Para usar el programa:"
echo "  🖥️  Interfaz gráfica:      python3 main.py"
echo "  ⌨️  Línea de comandos:    python3 main.py --file documento.pdf"
echo "  ❓  Mostrar ayuda:        python3 main.py --help"
echo ""
echo "💡 Tip: El programa está optimizado para funcionar con solo 4GB de RAM"
