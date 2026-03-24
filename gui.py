import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD
from CTkMessagebox import CTkMessagebox
from logic import elabora_documento_manga
import os
import fitz
import platform

class PDFMangaGUI(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        
        # Fix per Drag & Drop
        try:
            import tkinterdnd2
            base_path = os.path.dirname(tkinterdnd2.__file__)
            arch = 'win-x64' if platform.architecture()[0] == '64bit' else 'win-x86'
            dnd_path = os.path.join(base_path, 'tkdnd', arch)
            self.tk.call('lappend', 'auto_path', dnd_path)
            self.tk.call('package', 'require', 'tkdnd')
        except:
            pass

        self.title("PDF Fusion - Manga Mode")
        self.geometry("600x650")
        self.file_path = None
        self.crea_widget()

    def crea_widget(self):
        ctk.CTkLabel(self, text="📚 PDF Fusion Manga", font=("Roboto", 24, "bold")).pack(pady=20)

        # Area Drag and Drop
        self.drop_frame = ctk.CTkFrame(self, width=500, height=100, border_width=2, border_color="#3b8ed0")
        self.drop_frame.pack(pady=10, padx=20, fill="x")
        self.drop_frame.pack_propagate(False)
        self.label_drop = ctk.CTkLabel(self.drop_frame, text="Trascina qui il PDF")
        self.label_drop.pack(expand=True)
        
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.gestisci_drop)

        # BOTTONE VERDE SCURO
        # fg_color="#1b5e20" è un verde bosco scuro, hover_color="#144316" per il feedback al passaggio
        self.btn_import = ctk.CTkButton(
            self, 
            text="📁 Oppure Seleziona File", 
            command=self.seleziona_file, 
            fg_color="#1b5e20", 
            hover_color="#144316",
            font=("Roboto", 13, "bold")
        )
        self.btn_import.pack(pady=10)

        # Configurazione Slider
        self.label_start = ctk.CTkLabel(self, text="Pagina Iniziale: 1")
        self.label_start.pack(pady=(10, 0))
        self.slider_start = ctk.CTkSlider(self, from_=1, to=100, command=self.valida_slider)
        self.slider_start.pack(pady=5, padx=40, fill="x")

        self.label_end = ctk.CTkLabel(self, text="Pagina Finale: 1")
        self.label_end.pack(pady=(10, 0))
        self.slider_end = ctk.CTkSlider(self, from_=1, to=100, command=self.valida_slider)
        self.slider_end.pack(pady=5, padx=40, fill="x")

        # BARRA DI PROGRESSO (Inizialmente nascosta)
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.set(0)
        # Non usiamo .pack() qui, lo useremo solo durante l'esecuzione

        self.btn_avvia = ctk.CTkButton(self, text="Unisci in Stile Manga", command=self.esegui, state="disabled")
        self.btn_avvia.pack(pady=40)

    def carica_info_pdf(self, path):
        self.file_path = path
        try:
            doc = fitz.open(path)
            pagine = len(doc)
            doc.close()
            
            self.slider_start.configure(from_=1, to=pagine, number_of_steps=pagine-1)
            self.slider_end.configure(from_=1, to=pagine, number_of_steps=pagine-1)
            self.slider_start.set(1)
            self.slider_end.set(pagine)
            self.valida_slider()
            self.btn_avvia.configure(state="normal")
            self.label_drop.configure(text=f"File: {os.path.basename(path)}", text_color="#2ecc71")
        except Exception as e:
            CTkMessagebox(title="Errore", message=f"Errore PDF: {e}", icon="cancel")

    def valida_slider(self, _=None):
        s, e = int(self.slider_start.get()), int(self.slider_end.get())
        if s > e:
            self.slider_start.set(e)
            s = e
        self.label_start.configure(text=f"Pagina Iniziale: {s}")
        self.label_end.configure(text=f"Pagina Finale: {e}")

    def seleziona_file(self):
        path = ctk.filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if path: self.carica_info_pdf(path)

    def gestisci_drop(self, event):
        path = event.data.strip('{}')
        if path.lower().endswith('.pdf'): self.carica_info_pdf(path)

    def esegui(self):
        s, e = int(self.slider_start.get()), int(self.slider_end.get())
        
        # 1. Mostra la barra prima di iniziare
        self.progress_bar.pack(pady=10, padx=40, fill="x", before=self.btn_avvia)
        self.btn_avvia.configure(state="disabled")
        self.update() # Forza l'aggiornamento grafico

        try:
            out = elabora_documento_manga(self.file_path, s-1, e, self.progress_bar.set)
            CTkMessagebox(title="Successo", message=f"Creato: {out.name}", icon="check")
        except Exception as e:
            CTkMessagebox(title="Errore", message=str(e), icon="cancel")
        finally:
            # 2. Nascondi la barra quando ha finito
            self.progress_bar.set(0)
            self.progress_bar.pack_forget() 
            self.btn_avvia.configure(state="normal")