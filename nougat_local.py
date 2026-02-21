import os
import json
import time
import shutil
import datetime
import hashlib
import re
import sys
import subprocess
from pathlib import Path

# --- CONFIGURACION LOCAL ---
BASE_DIR = Path(os.getcwd())
STRUCTURE = {
    "input": BASE_DIR / "input",
    "output": BASE_DIR / "output",
    "failed": BASE_DIR / "failed",
    "checkpoint": BASE_DIR / "checkpoint"
}

# Crear directorios
for p in STRUCTURE.values():
    p.mkdir(parents=True, exist_ok=True)

REGISTRY_PATH = STRUCTURE["checkpoint"] / "registry.json"
LOG_PATH = STRUCTURE["checkpoint"] / "pipeline.log"

def log_message(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(f"[{timestamp}] {msg}")

# --- RASTREADOR DE ESTADO ---
class PipelineState:
    def __init__(self, path):
        self.path = path
        self.state = self._load()

    def _load(self):
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"processed": {}, "failed": {}}

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2)

    def is_processed(self, file_hash):
        return file_hash in self.state["processed"]

    def mark_success(self, file_hash, filename, output_path):
        self.state["processed"][file_hash] = {
            "filename": filename,
            "output": str(output_path),
            "timestamp": str(datetime.datetime.now())
        }
        self.save()

    def mark_failed(self, file_hash, filename, error):
        self.state["failed"][file_hash] = {
            "filename": filename,
            "error": str(error),
            "timestamp": str(datetime.datetime.now())
        }
        self.save()

def get_file_hash(path):
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

# --- POST-PROCESAMIENTO RAG ---
def extract_structured_data(mmd_path):
    with open(mmd_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    b = chr(92)
    # Usamos chr() para evitar problemas de escape en strings de Windows
    # Corregido: b*3 es necesario para encontrar \( y \[ escapados en el regex
    p_inline = b*3 + chr(40) + ".*?" + b*3 + chr(41)
    p_block = b*3 + chr(91) + ".*?" + b*3 + chr(93)
    equations = re.findall(f"{p_inline}|{p_block}", content, re.DOTALL)
    
    p_caption = chr(91) + "caption" + chr(93) + r".*?\n"
    captions = re.findall(p_caption, content)
    
    sections = []
    current_section = {"title": "Preliminares", "content": ""}
    # Normalizamos saltos de linea y dividimos
    for line in content.replace("\r\n", "\n").split("\n"):
        if line.startswith("# ") or line.startswith("## "):
            if current_section["content"].strip():
                sections.append(current_section)
            current_section = {"title": line.replace("#", "").strip(), "content": ""}
        else:
            current_section["content"] += line + "\n"
    if current_section["content"].strip():
        sections.append(current_section)

    return {
        "metadata": {
            "source": mmd_path.name,
            "processed_at": str(datetime.datetime.now()),
            "equation_count": len(equations),
            "section_count": len(sections)
        },
        "equations": equations,
        "captions": captions,
        "sections": sections
    }

def save_structured_json(mmd_path):
    try:
        structured_data = extract_structured_data(mmd_path)
        json_path = mmd_path.with_suffix(".json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(structured_data, f, indent=2, ensure_ascii=False)
        return json_path
    except Exception as e:
        log_message(f"Fallo en post-procesamiento para {mmd_path.name}: {e}")
        return None

# --- BUCLE PRINCIPAL ---
def get_nougat_cmd():
    # 1. Probar si esta en el PATH
    path_cmd = shutil.which("nougat")
    if path_cmd:
        log_message(f"Nougat encontrado en PATH: {path_cmd}")
        return path_cmd
    
    # 2. Probar rutas comunes en Windows
    appdata = os.environ.get("APPDATA")
    if appdata:
        python_scripts = Path(appdata) / "Python"
        if python_scripts.exists():
            log_message(f"Buscando nougat.exe en {python_scripts}...")
            for script_p in python_scripts.rglob("nougat.exe"):
                log_message(f"Nougat encontrado en: {script_p}")
                return str(script_p)
    
    # 3. Probar ruta especifica vista en logs
    target = Path(os.environ.get("APPDATA", "")) / "Python" / "Python311" / "Scripts" / "nougat.exe"
    if target.exists():
        log_message(f"Nougat encontrado en ruta fija: {target}")
        return str(target)

    log_message("ADVERTENCIA: No se encontro nougat.exe de forma automatica.")
    return "nougat" # Fallback

def main():
    nougat_cmd = get_nougat_cmd()
    state = PipelineState(REGISTRY_PATH)
    input_path = STRUCTURE["input"]
    all_files = [input_path / f for f in os.listdir(input_path) if f.lower().endswith(".pdf")]
    
    log_message(f"Se encontraron {len(all_files)} PDFs locales.")
    
    to_process = []
    for pdf_path in all_files:
        f_hash = get_file_hash(pdf_path)
        if state.is_processed(f_hash):
            continue
        to_process.append((pdf_path, f_hash))

    if not to_process:
        log_message("Nada nuevo que procesar.")
        return

    log_message(f"Iniciando procesamiento de {len(to_process)} archivos.")

    for pdf_path, f_hash in to_process:
        try:
            log_message(f"--- Procesando: {pdf_path.name} ---")
            
            # Ejecutar nougat via subprocess con ruta descubierta
            out_dir = str(STRUCTURE["output"])
            cmd = [nougat_cmd, str(pdf_path), "-o", out_dir, "--model", "0.1.0-small", "--no-skipping"]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Logueamos siempre la salida para depuracion
            if result.stdout:
                log_message(f"STDOUT Nougat:\n{result.stdout}")
            if result.stderr:
                log_message(f"STDERR Nougat:\n{result.stderr}")

            if result.returncode != 0:
                raise Exception(f"Nougat falló con código {result.returncode}")

            expected_md = STRUCTURE["output"] / f"{pdf_path.stem}.mmd"
            if expected_md.exists():
                save_structured_json(expected_md)
                state.mark_success(f_hash, pdf_path.name, expected_md)
                log_message(f"Exito: {pdf_path.name}")
            else:
                # Comprobar si Nougat generó el archivo con otro nombre o en otra carpeta
                log_message(f"AVISO: {expected_md} no encontrado. Contenido de {STRUCTURE['output']}: {os.listdir(STRUCTURE['output'])}")
                raise Exception("Archivo .mmd no generado.")
                
        except Exception as e:
            log_message(f"Error en {pdf_path.name}: {e}")
            state.mark_failed(f_hash, pdf_path.name, str(e))
            shutil.move(str(pdf_path), str(STRUCTURE["failed"] / pdf_path.name))

if __name__ == "__main__":
    main()
