import re
import os
from pathlib import Path

def mmd_to_latex_fallback(mmd_content, title="Export", language="spanish"):
    preamble = [
        "\\documentclass[11pt,a4paper]{article}",
        "\\usepackage[utf8]{inputenc}",
        "\\usepackage[T1]{fontenc}",
        f"\\usepackage[{language}]{{babel}}",
        "\\usepackage{amsmath,amssymb,amsfonts}",
        "\\usepackage{graphicx}",
        "\\usepackage{geometry}",
        "\\geometry{margin=1in}",
        "\\title{" + title + "}",
        "\\author{Pipeline Nougat OCR}",
        "\\date{\\today}",
        "\\begin{document}",
        "\\maketitle",
        "\\tableofcontents",
        "\\newpage"
    ]
    
    protected_math = []
    def save_math(m):
        protected_math.append(m.group(0))
        return f"MATHPROTECT{len(protected_math)-1}Z"
    
    body = mmd_content
    body = re.sub(r'\[MISSING_PAGE_EMPTY:\d+\]', '', body)
    body = re.sub(r'\[MISSING_PAGE_FAIL:\d+\]', r'\\begin{center}\\textbf{[ERROR: Pagina no procesada en el original]}\\end{center}', body)
    
    # Marcamos entornos matemáticos y comandos estructurales clave para evitar que sean escapados
    body = re.sub(
        r'\\\(.*?\\\)|\\\[.*?\\\]|\\cite\{.*?\}|\\ref\{.*?\}|\\label\{.*?\}|\\begin\{.*?\}|\\end\{.*?\}',
        save_math,
        body,
        flags=re.DOTALL
    )

    raw_cmds_map = {
        r'\\section\*?\{([^{}]*)\}': r'LSECS\1LEND',
        r'\\subsection\*?\{([^{}]*)\}': r'LSUBS\1LEND',
        r'\\subsubsection\*?\{([^{}]*)\}': r'LSUBSUBS\1LEND',
        r'\\paragraph\*?\{([^{}]*)\}': r'LPARAGS\1LEND',
        r'\\subparagraph\*?\{([^{}]*)\}': r'LSTARTPAGS\1LEND',
        r'\\textbf\{([^{}]*)\}': r'LBOLDS\1LEND',
        r'\\textit\{([^{}]*)\}': r'LITALS\1LEND',
        r'\\underline\{([^{}]*)\}': r'LBOLDS\1LEND'
    }
    for _ in range(5):
        any_change = False
        for cmd_rec, marker_sub in raw_cmds_map.items():
            new_body, count = re.subn(cmd_rec, marker_sub, body, flags=re.DOTALL)
            if count > 0:
                body = new_body
                any_change = True
        if not any_change: break

    body = re.sub(r'^###### (.*)', r'LSTARTPAGS\1LEND', body, flags=re.MULTILINE)
    body = re.sub(r'^##### (.*)', r'LSTARTPAGS\1LEND', body, flags=re.MULTILINE)
    body = re.sub(r'^#### (.*)', r'LPARAGS\1LEND', body, flags=re.MULTILINE)
    body = re.sub(r'^### (.*)', r'LSUBSUBS\1LEND', body, flags=re.MULTILINE)
    body = re.sub(r'^## (.*)', r'LSUBS\1LEND', body, flags=re.MULTILINE)
    body = re.sub(r'^# (.*)', r'LSECS\1LEND', body, flags=re.MULTILINE)
    
    body = re.sub(r'\*\*(.*?)\*\*', r'LBOLDS\1LEND', body)
    body = re.sub(r'\*(.*?)\*', r'LITALS\1LEND', body)
    body = re.sub(r'_(.*?)_', r'LITALS\1LEND', body)

    special_chars = {
        '&': r'\&', '%': r'\%', '$': r'\$', '_': r'\_', 
        '{': r'\{', '}': r'\}', '#': r'\#', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'
    }
    
    for char, replacement in special_chars.items():
        body = body.replace(char, replacement)

    body = body.replace("LSECS", r"\section{")
    body = body.replace("LSUBSUBS", r"\subsubsection{")
    body = body.replace("LSUBS", r"\subsection{")
    body = body.replace("LPARAGS", r"\paragraph{")
    body = body.replace("LSTARTPAGS", r"\subparagraph{")
    body = body.replace("LBOLDS", r"\textbf{")
    body = body.replace("LITALS", r"\textit{")
    body = body.replace("LEND", "}") 

    lines = body.split('\n')
    new_lines = []
    in_list = False
    for line in lines:
        if line.strip().startswith('\\* '): 
            if not in_list:
                new_lines.append('\\begin{itemize}')
                in_list = True
            new_lines.append('  \\item ' + line.strip()[3:])
        else:
            if in_list:
                new_lines.append('\\end{itemize}')
                in_list = False
            new_lines.append(line)
    if in_list: new_lines.append('\\end{itemize}')
    body = '\n'.join(new_lines)

    def restore_math(m):
        idx = int(m.group(1))
        return protected_math[idx] if idx < len(protected_math) else m.group(0)
    
    body = re.sub(r'MATHPROTECT(\d+)Z', restore_math, body)
    
    full_doc = '\n'.join(preamble) + '\n' + body + '\n\\end{document}'
    return full_doc

def mmd_to_latex(mmd_content, title="Export", language="spanish"):
    try:
        import pypandoc
        try:
            pypandoc.get_pandoc_path()
        except OSError:
            print("Pandoc no encontrado en el sistema. Descargando versión interna...")
            pypandoc.download_pandoc()

        body = mmd_content
        body = re.sub(r'\[MISSING_PAGE_EMPTY:\d+\]', '', body)
        body = re.sub(r'\[MISSING_PAGE_FAIL:\d+\]', '\n\n**[ERROR: Página no procesada en el original]**\n\n', body)

        # Convertir delimitadores \( \) y \[ \] a $ y $$ para que Pandoc reconozca las ecuaciones
        body = body.replace(r'\(', '$').replace(r'\)', '$')
        body = body.replace(r'\[', '$$').replace(r'\]', '$$')

        lang_map = {
            "spanish": "es",
            "english": "en"
        }
        lang_code = lang_map.get(language.lower(), language)

        latex_code = pypandoc.convert_text(
            body,
            to='latex',
            format='markdown',
            extra_args=[
                '--standalone',
                '-V', f'lang={lang_code}',
                '-V', f'title={title}',
                '-V', 'author=Pipeline Nougat OCR',
                '-V', 'geometry:margin=1in'
            ]
        )
        return latex_code
    except Exception as e:
        print(f"Fallo en la conversión con Pandoc ({e}). Usando conversor de respaldo (Regex)...")
        return mmd_to_latex_fallback(mmd_content, title, language)

def recover_missing_pages(pdf_path, mmd_content, language="spanish"):
    missing_pages = re.findall(r'\[MISSING_PAGE_(EMPTY|FAIL):(\d+)\]', mmd_content)
    if not missing_pages:
        return mmd_content
        
    try:
        import pypdfium2 as pdfium
        import pytesseract
    except ImportError:
        print("Aviso: 'pytesseract' o 'pypdfium2' no están disponibles. Saltando recuperación OCR.")
        return mmd_content

    # Mapear idioma
    tess_lang = "spa+eng" if language.lower() == "spanish" else "eng"
    
    modified_content = mmd_content
    try:
        src_pdf = pdfium.PdfDocument(str(pdf_path))
        for flag_type, pg_num_str in missing_pages:
            pg_idx = int(pg_num_str) - 1
            if pg_idx < 0 or pg_idx >= len(src_pdf): continue
            
            print(f"Recuperando página {pg_num_str} vía Tesseract OCR...")
            page = src_pdf[pg_idx]
            bitmap = page.render(scale=2)
            img = bitmap.to_pil()
            
            try:
                ocr_text = pytesseract.image_to_string(img, lang=tess_lang).strip()
            except Exception as ocr_err:
                print(f"No se pudo ejecutar Tesseract en la página {pg_num_str}: {ocr_err}")
                ocr_text = None
                
            if ocr_text:
                replacement = f"\n\n> [!NOTE]\n> **[PÁGINA {pg_num_str} RECUPERADA VÍA OCR TESSERACT]**\n>\n"
                indented_text = "\n".join([f"> {line}" for line in ocr_text.split("\n")])
                replacement += indented_text + "\n\n"
                
                target_tag = f"[MISSING_PAGE_{flag_type}:{pg_num_str}]"
                modified_content = modified_content.replace(target_tag, replacement)
                print(f"Página {pg_num_str} recuperada e inyectada con éxito.")
    except Exception as e:
        print(f"Error en recuperación de páginas: {e}")
        
    return modified_content

def generate_blank_page_report(pdf_path, mmd_content, output_pdf_report):
    try:
        import pypdfium2 as pdfium
        from fpdf import FPDF
    except ImportError:
        print("Error: Se requiere 'fpdf2' para generar el reporte de auditoria.")
        return False

    missing_pages = re.findall(r'\[MISSING_PAGE_EMPTY:(\d+)\]', mmd_content)
    if not missing_pages:
        return False

    temp_dir = Path("temp_audit")
    temp_dir.mkdir(exist_ok=True)
    try:
        pdf = FPDF()
        src_pdf = pdfium.PdfDocument(str(pdf_path))
        for pg_num_str in missing_pages:
            pg_idx = int(pg_num_str) - 1
            if pg_idx < 0 or pg_idx >= len(src_pdf): continue
            pdf.add_page()
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, f'Evidencia de Pagina Original: {pg_num_str}', 0, 1)
            page = src_pdf[pg_idx]
            bitmap = page.render(scale=2)
            img = bitmap.to_pil()
            img_path = temp_dir / f"page_{pg_num_str}.png"
            img.save(img_path)
            pdf.image(str(img_path), x=10, y=30, w=190)
            
        pdf.output(str(output_pdf_report))
        return True
    finally:
        for f in temp_dir.glob("*.png"):
            try:
                os.remove(f)
            except Exception:
                pass
        try:
            temp_dir.rmdir()
        except Exception:
            pass
