# Nougat OCR Pipeline: Mathematical PDF to Markdown

Este repositorio contiene un pipeline optimizado para la conversion de documentos PDF a formatos estructurados como Markdown (.mmd) y JSON. Basado en el modelo Nougat de Meta AI.

## Caracteristicas Principales

### Estabilizacion de Dependencias
El sistema incluye parches para asegurar la compatibilidad entre versiones de las siguientes librerias:
- **Transformers**: Resolucion de conflictos en la clase de configuracion.
- **Albumentations/Pydantic**: Correccion de esquemas de validacion para la compresion de imagenes.
- **pypdfium2**: Adaptacion para soporte multiversion en entornos Windows y Linux.

### Optimizacion de Recuperacion
Se ha implementado el flag `--no-skipping` para desactivar el heuristico de Nougat que descarta paginas ante la deteccion de repeticiones de texto. Esto asegura la captura de contenido en diagramas complejos o tablas densas.

### Salida Orientada a RAG
Ademas del Markdown estandar, el pipeline genera archivos JSON con:
- Metadatos de ecuaciones (conteo y extraccion).
- Estructura de secciones.
- Capturas de subtitulos de figuras.

## Componentes del Proyecto

1. **nougat_local.py**: Script principal para ejecucion en sistemas locales (Windows/Linux).
2. **nougat_pipeline.ipynb**: Notebook optimizado para ejecucion en Google Colab con soporte para GPU T4.
3. **build_notebook.py**: Script generador para mantener la integridad del notebook y sus parches.
4. **local_setup.bat**: Instalador automatizado de entorno para Windows.

## Instalacion y Uso

### Entorno Local (Windows)
1. Ejecutar `local_setup.bat` para configurar las dependencias de Python.
2. Colocar los archivos PDF en la carpeta `input/`.
3. Ejecutar `python nougat_local.py`.
4. Los resultados se encontraran en la carpeta `output/`.

### Google Colab
1. Subir `nougat_pipeline.ipynb` a Google Colab.
2. Asegurarse de utilizar un entorno con GPU (T4 o superior).
3. Seguir los pasos numerados dentro del notebook.

## Estructura de Datos
El pipeline organiza los archivos de la siguiente manera:
- `/input`: PDFs por procesar.
- `/output`: Archivos .mmd y .json generados.
- `/failed`: PDFs que presentaron errores durante el proceso.
- `/checkpoint`: Registro de estado (registry.json) y logs de operacion.
