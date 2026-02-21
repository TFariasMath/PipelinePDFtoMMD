@echo off
setlocal

echo --- Instalador del Pipeline de Nougat Local ---
echo Se requiere Python instalado en el sistema.

:: 1. Crear entorno virtual
if not exist venv (
    echo Creando entorno virtual...
    python -m venv venv
)

:: 2. Instalar dependencias
echo Instalando dependencias seguras...
call venv\Scripts\activate
pip install --force-reinstall transformers==4.38.2
pip install nougat-ocr pypdf torch tqdm albumentations==1.3.1 pydantic<2.0 opencv-python-headless

:: 3. Aplicar Patch Quirurgico localmente
echo Aplicando parche de compatibilidad en Nougat...
python -c "import site; from pathlib import Path; [((p := Path(d)/'nougat'/'model.py').write_text(p.read_text().replace('PretrainedConfig', 'PreTrainedConfig')) if p.exists() else None) for d in site.getsitepackages()]"

:: 4. Crear carpetas de estructura
if not exist input mkdir input
if not exist output mkdir output
if not exist failed mkdir failed
if not exist checkpoint mkdir checkpoint

echo.
echo --- Instalacion Completada ---
echo Pasos:
echo 1. Pon tus PDF en la carpeta 'input'
echo 2. Ejecuta: call venv\Scripts\activate
echo 3. Ejecuta: python nougat_local.py
pause
