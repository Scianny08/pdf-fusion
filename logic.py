from pypdf import PdfReader, PdfWriter
from pathlib import Path

def elabora_documento_pdf(percorso_input, intervallo, stile, callback_progresso=None):
    """Gestisce la manipolazione fisica del PDF."""
    reader = PdfReader(percorso_input)
    writer = PdfWriter()
    pagine_totali = len(reader.pages)
    
    indice_corrente = 0
    attivo = True
    
    while attivo:
        if indice_corrente >= pagine_totali:
            attivo = False
        else:
            fine_blocco = min(indice_corrente + intervallo, pagine_totali)
            blocco = [reader.pages[i] for i in range(indice_corrente, fine_blocco)]
            
            if stile == "Orientale (RTL)":
                blocco.reverse()
            
            for pagina in blocco:
                writer.add_page(pagina)
            
            indice_corrente += intervallo
            
            # Notifica la GUI per aggiornare la barra
            if callback_progresso:
                callback_progresso(min(indice_corrente / pagine_totali, 1.0))

    # Salvataggio
    file_info = Path(percorso_input)
    percorso_output = file_info.parent / f"{file_info.stem} (merged){file_info.suffix}"
    
    with open(percorso_output, "wb") as f_out:
        writer.write(f_out)
    
    return percorso_output
