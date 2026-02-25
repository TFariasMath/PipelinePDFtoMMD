# Nougat OCR Pipeline

Pipeline optimizado para la conversion de documentos PDF a formatos estructurados (Markdown/JSON/LaTeX) enfocada en contenido cientifico y matematico.

## Core Capabilities

### Estabilizacion de Dependencias
Implementacion de parches quirurgicos para asegurar la compatibilidad entre versiones criticas:
- **Transformers**: Resolucion de conflictos en `PreTrainedConfig`.
- **Albumentations/Pydantic**: Correccion de validacion en esquemas de compresion de imagenes.
- **pypdfium2**: Soporte multiversion para renderizado en Windows/Linux.

### Optimizacion de Recuperacion
Uso del flag `--no-skipping` para desactivar heuristicos de Nougat que descartan contenido ante repeticiones tectuales, asegurando la integridad en diagramas y tablas densas.

### Salidas Generadas
- **Markdown (.mmd)**: Salida cruda de Nougat.
- **LaTeX (.tex)**: Documento estructurado listo para compilacion academica.
- **Audit Report (PDF)**: Verificacion visual dinamica de paginas detectadas como vacias.
- **JSON**: Metadatos de ecuaciones y secciones para ingesta RAG.

## Setup y Uso

### Local (Windows)
1. Instalar dependencias: `local_setup.bat`.
2. PDFs en carpeta `input/`.
3. Ejecutar: `python nougat_local.py`.

### Cloud (Colab)
1. Cargar `nougat_pipeline.ipynb`.
2. Activar T4 GPU.
3. Seguir celdas de configuracion.

## Folder Structure
- `/input`: Fuente.
- `/output`: Resultados (.mmd, .json, .tex, .pdf).
- `/failed`: Captura de errores de procesamiento.
- `/checkpoint`: Persistencia y logs.
