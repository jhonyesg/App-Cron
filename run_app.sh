#!/bin/bash

# Ruta del proyecto
PROJECT_DIR="/home/jsuarez/Nextcloud/99_Multimedia/RTMP/Linea_Stream/linea_backup/App Cron"
# Ruta del entorno virtual fuera del proyecto
VENV_PATH="$HOME/.venv_cronapp"

# Imprimir mensaje inicial
echo "Iniciando el despliegue de la aplicación..."

# Cambiar al directorio del proyecto
echo "Cambiando al directorio del proyecto: $PROJECT_DIR"
cd "$PROJECT_DIR"
echo "Directorio cambiado a $(pwd)."

# Verificar si el entorno virtual existe fuera del proyecto
if [ ! -d "$VENV_PATH" ]; then
    echo "El entorno virtual no existe en $VENV_PATH. Creándolo..."
    python3 -m venv "$VENV_PATH"
    echo "Entorno virtual creado en $VENV_PATH."
fi

# Instalar dependencias usando el pip del entorno virtual externo
echo "Instalando dependencias..."
"$VENV_PATH/bin/pip" install --upgrade pip
"$VENV_PATH/bin/pip" install -r "requirements.txt"

# Ejecutar la aplicación Flask usando el python del entorno virtual externo
echo "Ejecutando la aplicación Flask..."
"$VENV_PATH/bin/python" app.py

echo "Aplicación ejecutada correctamente."
