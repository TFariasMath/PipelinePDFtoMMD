@echo off
setlocal

echo Nougat Local Pipeline Setup
echo Python required.

if not exist venv (
    echo Virtualenv...
    python -m venv venv
)

echo Dependencies...
call venv\Scripts\activate
pip install --force-reinstall transformers==4.38.2
pip install nougat-ocr pypdf torch tqdm transformers==4.38.2 albumentations==1.4.3 pypdfium2 fpdf2 pydantic<2.0 opencv-python-headless

echo Patches...
python -c "import site; import os; from pathlib import Path; paths = [Path(p) for p in site.getsitepackages() if 'site-packages' in p]; [(p := (base/'nougat'/'model.py')).write_text(p.read_text().replace('PretrainedConfig', 'PreTrainedConfig')) if p.exists() else None for base in paths]"

if not exist input mkdir input
if not exist output mkdir output
if not exist failed mkdir failed
if not exist checkpoint mkdir checkpoint

echo.
echo Process:
echo 1. PDFs -> 'input'
echo 2. call venv\Scripts\activate
echo 3. python nougat_local.py
pause
