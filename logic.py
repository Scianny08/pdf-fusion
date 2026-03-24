import fitz  # PyMuPDF
from pathlib import Path

def elabora_documento_manga(percorso_input, start_page, end_page, callback_progresso=None):
    """
    Processa il PDF mantenendo TUTTE le pagine:
    - Pagine prima del range: Singole
    - Pagine nel range: Unite a coppie (Manga)
    - Pagine dopo il range: Singole
    """
    doc = fitz.open(percorso_input)
    pdf_writer = fitz.open()
    totale_doc = len(doc)
    
    # 1. COPIA LE PAGINE PRIMA DEL RANGE (SINGOLE)
    for i in range(0, start_page):
        page = doc[i]
        new_page = pdf_writer.new_page(width=page.rect.width, height=page.rect.height)
        new_page.show_pdf_page(page.rect, doc, i)
        if callback_progresso: callback_progresso((i + 1) / totale_doc * 0.3)

    # 2. UNISCE LE PAGINE NEL RANGE (COPPIE MANGA)
    pagine_range = list(range(start_page, end_page))
    i = 0
    while i < len(pagine_range):
        idx_destra = pagine_range[i]
        
        if i + 1 < len(pagine_range):
            # C'è una coppia: Uniscile
            idx_sinistra = pagine_range[i + 1]
            p_r, p_l = doc[idx_destra], doc[idx_sinistra]
            
            new_w = p_r.rect.width + p_l.rect.width
            new_h = max(p_r.rect.height, p_l.rect.height)
            
            new_page = pdf_writer.new_page(width=new_w, height=new_h)
            # Manga: Sinistra (p_l) e poi Destra (p_r)
            new_page.show_pdf_page(fitz.Rect(0, 0, p_l.rect.width, p_l.rect.height), doc, idx_sinistra)
            new_page.show_pdf_page(fitz.Rect(p_l.rect.width, 0, new_w, p_r.rect.height), doc, idx_destra)
            i += 2
        else:
            # Pagina singola rimasta nel range
            page = doc[idx_destra]
            new_page = pdf_writer.new_page(width=page.rect.width, height=page.rect.height)
            new_page.show_pdf_page(page.rect, doc, idx_destra)
            i += 1
        
        if callback_progresso: callback_progresso(0.3 + (i / len(pagine_range) * 0.4))

    # 3. COPIA LE PAGINE DOPO IL RANGE (SINGOLE)
    for i in range(end_page, totale_doc):
        page = doc[i]
        new_page = pdf_writer.new_page(width=page.rect.width, height=page.rect.height)
        new_page.show_pdf_page(page.rect, doc, i)
        if callback_progresso: callback_progresso(0.7 + ((i - end_page + 1) / (totale_doc - end_page) * 0.3))

    # Salvataggio
    output_path = Path(percorso_input).parent / f"{Path(percorso_input).stem}_completo_manga.pdf"
    pdf_writer.save(str(output_path))
    pdf_writer.close()
    doc.close()
    return output_path