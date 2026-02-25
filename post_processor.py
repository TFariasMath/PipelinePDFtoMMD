import re
import os
from pathlib import Path

def mmd_to_latex(mmd_content, title="Export"):
    preamble = [
        "\\documentclass[11pt,a4paper]{article}",
        "\\usepackage[utf8]{inputenc}",
        "\\usepackage[T1]{fontenc}",
        "\\usepackage[spanish]{babel}",
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
    
    # 1. Protección de Matemáticas (Intocables)
    protected_math = []
    def save_math(m):
        protected_math.append(m.group(0))
        return f"MATHPROTECT{len(protected_math)-1}Z"
    
    body = mmd_content
    body = re.sub(r'\[MISSING_PAGE_EMPTY:\d+\]', '', body)
    body = re.sub(r'\[MISSING_PAGE_FAIL:\d+\]', r'\\begin{center}\\textbf{[ERROR: Pagina no procesada en el original]}\\end{center}', body)
    
    # Marcamos entornos matemáticos
    body = re.sub(r'\\\(.*?\\\)|\\\[.*?\\\]', save_math, body, flags=re.DOTALL)

    # Identificamos comandos comunes que Nougat suele poner y los convertimos a nuestros marcadores
    # Usamos un bucle para manejar anidación (ej. \section{...\textbf{...}}) de adentro hacia afuera
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

    # 2. Marcaje de Estructuras Markdown
    body = re.sub(r'^###### (.*)', r'LSTARTPAGS\1LEND', body, flags=re.MULTILINE)
    body = re.sub(r'^##### (.*)', r'LSTARTPAGS\1LEND', body, flags=re.MULTILINE)
    body = re.sub(r'^#### (.*)', r'LPARAGS\1LEND', body, flags=re.MULTILINE)
    body = re.sub(r'^### (.*)', r'LSUBSUBS\1LEND', body, flags=re.MULTILINE)
    body = re.sub(r'^## (.*)', r'LSUBS\1LEND', body, flags=re.MULTILINE)
    body = re.sub(r'^# (.*)', r'LSECS\1LEND', body, flags=re.MULTILINE)
    
    # Formatos (Non-greedy)
    body = re.sub(r'\*\*(.*?)\*\*', r'LBOLDS\1LEND', body)
    body = re.sub(r'\*(.*?)\*', r'LITALS\1LEND', body)

    # 3. Escape de Caracteres Especiales (en todo el cuerpo, incluyendo títulos marcados)
    special_chars = {
        '&': r'\&', '%': r'\%', '$': r'\$', '_': r'\_', 
        '{': r'\{', '}': r'\}', '#': r'\#', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'
    }
    
    for char, replacement in special_chars.items():
        body = body.replace(char, replacement)

    # 4. Finalización de Marcadores a LaTeX
    body = body.replace("LSECS", r"\section{")
    body = body.replace("LSUBS", r"\subsection{")
    body = body.replace("LSUBSUBS", r"\subsubsection{")
    body = body.replace("LPARAGS", r"\paragraph{")
    body = body.replace("LSTARTPAGS", r"\subparagraph{")
    body = body.replace("LBOLDS", r"\textbf{")
    body = body.replace("LITALS", r"\textit{")
    body = body.replace("LEND", "}") 

    # 5. Listas
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

    # 6. Restaurar Matemáticas
    def restore_math(m):
        idx = int(m.group(1))
        return protected_math[idx] if idx < len(protected_math) else m.group(0)
    
    body = re.sub(r'MATHPROTECT(\d+)Z', restore_math, body)
    
    full_doc = '\n'.join(preamble) + '\n' + body + '\n\\end{document}'
    return full_doc

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

    pdf = FPDF()
    src_pdf = pdfium.PdfDocument(str(pdf_path))
    temp_dir = Path("temp_audit")
    temp_dir.mkdir(exist_ok=True)

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
    for f in temp_dir.glob("*.png"): os.remove(f)
    temp_dir.rmdir()
    return True
