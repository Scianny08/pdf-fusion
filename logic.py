import fitz  # PyMuPDF
from pathlib import Path
import os

def get_documents_path():
    """Ritorna il percorso della cartella Documenti dell'utente su Windows, macOS o Linux."""
    home = Path.home()
    try:
        # Tenta di recuperare il percorso standard su Linux tramite xdg-user-dir
        xdg_docs = os.popen('xdg-user-dir DOCUMENTS').read().strip()
        if xdg_docs and os.path.exists(xdg_docs): return Path(xdg_docs)
    except:
        pass
    
    # Fallback per nomi comuni della cartella documenti
    for folder in ["Documents", "Documenti", "Documentos"]:
        if (home / folder).exists(): return home / folder
    return home

def elabora_documento(lista_task, manga_mode=True, callback_progresso=None):
    """
    Elabora ogni PDF separatamente applicando l'affiancamento e le esclusioni.
    """
    totale_file = len(lista_task)
    output_dir = get_documents_path() / "pdf-page-merger"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    ultimo_output = None

    for idx, task in enumerate(lista_task):
        # Reset: creiamo un nuovo documento PDF vuoto per ogni file in lista
        pdf_writer = fitz.open() 
        
        path = task['path']
        start = task['start']
        end = task['end']
        excluded = task.get('exclude', set()) # Set di indici 0-based da saltare
        
        current_file = Path(path)
        doc = fitz.open(path)
        
        # --- 1. Pagine Singole Pre-Range (es. Copertina) ---
        for p in range(0, start):
            if p not in excluded and p < len(doc):
                pdf_writer.insert_pdf(doc, from_page=p, to_page=p)
            
        # --- 2. Elaborazione Pagine Affiancate (Range Selezionato) ---
        # Filtriamo le pagine nel range rimuovendo quelle escluse
        pagine_valide = [p for p in range(start, end) if p not in excluded and p < len(doc)]
        
        i = 0
        while i < len(pagine_valide):
            idx_1 = pagine_valide[i]
            
            # Se c'è una pagina successiva disponibile, le affianchiamo
            if i + 1 < len(pagine_valide):
                idx_2 = pagine_valide[i + 1]
                p1, p2 = doc[idx_1], doc[idx_2]
                
                # Calcoliamo le dimensioni della nuova pagina (Larghezza combinata, Altezza massima)
                nw = p1.rect.width + p2.rect.width
                nh = max(p1.rect.height, p2.rect.height)
                new_page = pdf_writer.new_page(width=nw, height=nh)
                
                if manga_mode: # Stile Orientale: DX -> SX
                    # La seconda pagina va a sinistra (0,0), la prima a destra (p2.width, 0)
                    new_page.show_pdf_page(fitz.Rect(0, 0, p2.rect.width, p2.rect.height), doc, idx_2)
                    new_page.show_pdf_page(fitz.Rect(p2.rect.width, 0, nw, p1.rect.height), doc, idx_1)
                else: # Stile Occidentale: SX -> DX
                    # La prima pagina va a sinistra (0,0), la seconda a destra (p1.width, 0)
                    new_page.show_pdf_page(fitz.Rect(0, 0, p1.rect.width, p1.rect.height), doc, idx_1)
                    new_page.show_pdf_page(fitz.Rect(p1.rect.width, 0, nw, p2.rect.height), doc, idx_2)
                i += 2
            else:
                # Se rimane una pagina sola (dispari), la inseriamo singola
                pdf_writer.insert_pdf(doc, from_page=idx_1, to_page=idx_1)
                i += 1
                
        # --- 3. Pagine Singole Post-Range (es. Extra/Crediti) ---
        for p in range(end, len(doc)):
            if p not in excluded:
                pdf_writer.insert_pdf(doc, from_page=p, to_page=p)
            
        # --- Salvataggio del file elaborato ---
        suffisso = "- ORIENTALE" if manga_mode else "- OCCIDENTALE"
        output_path = output_dir / f"{current_file.stem} {suffisso}.pdf"
        
        pdf_writer.save(str(output_path))
        pdf_writer.close()
        doc.close()
        
        ultimo_output = output_path
        
        # Aggiornamento barra di progresso nella GUI
        if callback_progresso:
            callback_progresso((idx + 1) / totale_file)

    return ultimo_output