# Pipeline Nougat OCR para PDF a Markdown/LaTeX

Este repositorio contiene un pipeline optimizado y de alta tolerancia a fallos para procesar documentos PDF científicos y matemáticos complejos, convirtiéndolos a formatos estructurados: **Markdown (`.mmd`)**, **LaTeX (`.tex`)** y **JSON RAG**. 

El pipeline está diseñado para ejecutarse tanto localmente en Windows como en la nube mediante Google Colab.

---

## 🚀 Características Principales

### 1. Robustez de Almacenamiento (Fallback de Google Drive)
* **Colab Nativo:** Evalúa de forma dinámica si el almacenamiento de Google Drive (`/content/drive`) está montado y autorizado.
* **Respaldo Automático:** Si la conexión a Drive falla o se omite, los archivos de entrada/salida se redirigen automáticamente a una estructura de carpetas locales seguras dentro del contenedor de Colab (`/content/NovaLibrary`), previniendo caídas del pipeline.

### 2. Recuperación de Páginas Omitidas (Tesseract OCR)
* **El Problema:** El motor Nougat a veces marca páginas complejas o con mucho texto plano como vacías (`[MISSING_PAGE_EMPTY]`), dejándolas en blanco en el resultado final.
* **Nuestra Solución:** Una rutina post-procesadora que escanea el archivo Markdown generado. Si detecta páginas omitidas, renderiza la página original a imagen mediante `pypdfium2` y le aplica **Tesseract OCR** (con soporte multilingüe en español e inglés). El texto recuperado se inyecta directamente de vuelta en el flujo del documento.

### 3. Conversión LaTeX Inteligente y Tolerante a Fallos (Pandoc + Regex Fallback)
* **Conversión Principal (Pandoc):** Convierte el Markdown enriquecido a un código LaTeX limpio y estructurado de calidad editorial. En Google Colab, se utiliza el paquete `pypandoc-binary` para garantizar que la compilación de Pandoc funcione de forma 100% autónoma y no dependa de instalaciones externas del sistema.
* **Conversor de Respaldo (Regex Fallback):** Si Pandoc no se encuentra disponible en la máquina local o falla, el procesador activa automáticamente un convertidor basado en expresiones regulares.
* **Parches de Estructura:**
  * **Títulos correctos:** Resuelto el bug de precedencia de reemplazo (`LSUBSUBS` vs `LSUBS`), garantizando subsubsecciones (`\subsubsection`) limpias y sin texto corrupto.
  * **Cursivas correctas:** El procesador traduce las cursivas delimitadas por guiones bajos (`_texto_`) nativas de Nougat en bloques LaTeX correctos (`\textit{}` / `\emph{}`), evitando guiones bajos escapados (`\_`) en el texto plano.

### 4. JSON Estructurado para Sistemas RAG
* Separa metadatos del documento, una lista limpia de todas las ecuaciones detectadas para búsquedas rápidas, y la jerarquía estructurada de los textos de cada capítulo lista para alimentar bases de datos vectoriales.

---

## 📂 Estructura de Carpetas

El pipeline espera y mantiene la siguiente jerarquía de directorios (tanto local como en Drive/Colab):
* `/input`: Coloca aquí tus PDFs a procesar.
* `/output`: Carpeta donde se guardan los resultados (`.mmd`, `.json`, `.tex`).
* `/failed`: PDFs que arrojaron un error crítico durante el procesamiento.
* `/checkpoint`: Logs y persistencia del estado de procesamiento.

---

## 🛠️ Instrucciones de Setup y Uso

### A. Ejecución en la Nube (Google Colab - Recomendado)
1. Carga el cuaderno [nougat_pipeline.ipynb](nougat_pipeline.ipynb) en Google Colab.
2. Asegúrate de activar el entorno de ejecución con **GPU (T4)**.
3. Ejecuta la celda **1. Instalación de Dependencias** (instalará automáticamente Tesseract, Pandoc y los binarios necesarios).
4. Configura las rutas (por defecto, buscará la carpeta `NovaLibrary` en tu Google Drive) y ejecuta el pipeline.

### B. Ejecución Local (Windows)
1. Instala las dependencias ejecutando: `local_setup.bat`.
2. Coloca tus archivos PDF en la carpeta `/input`.
3. Ejecuta el procesador:
   ```bash
   python nougat_local.py
   ```

---

## 📝 Contribuciones y Correcciones
Este pipeline ha sido optimizado colaborativamente para garantizar código LaTeX limpio listo para compilar directamente en plataformas como **Overleaf** sin errores de caracteres especiales ni problemas de preámbulo.
