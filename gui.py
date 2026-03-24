import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD
from CTkMessagebox import CTkMessagebox
from logic import elabora_documento_pdf # Importiamo la logica
import os

class PDFFusionGUI(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        self.TkdndVersion = TkinterDnD._path_to_get_tkdnd(self)
        super().__init__()
        self.title("PDF Fusion")
        self.geometry("600x550")
        
        # Variabili e Setup UI (uguale a prima...)
        self.file_path_var = ctk.StringVar(value="Nessun file selezionato")
        self.interval_var = ctk.StringVar(value="2")
        self.style_var = ctk.StringVar(value="Occidentale (LTR)")
        self.crea_widget()

    def crea_widget(self):
        # ... (Qui inseriresti tutto il codice dei pulsanti/layout visto prima)
        # Per brevità, assumiamo che il pulsante 'Avvia' chiami self.avvia_processo
        self.btn_avvia = ctk.CTkButton(self, text="Elabora", command=self.avvia_processo)
        self.btn_avvia.pack(pady=20)
        
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=10)

    def avvia_processo(self):
        try:
            intervallo = int(self.interval_var.get())
            percorso = self.file_path_var.get()
            
            # Chiamiamo la funzione dal file logic.py
            output = elabora_documento_pdf(
                percorso, 
                intervallo, 
                self.style_var.get(),
                callback_progresso=self.aggiorna_barra
            )
            
            CTkMessagebox(title="Fatto", message=f"Salvato in: {output.name}", icon="check")
        except Exception as e:
            CTkMessagebox(title="Errore", message=str(e), icon="cancel")

    def aggiorna_barra(self, valore):
        self.progress_bar.set(valore)
        self.update_idletasks()
