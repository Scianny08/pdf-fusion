import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD
from CTkMessagebox import CTkMessagebox
from logic import elabora_documento
import os, fitz, sys, re

class PDFItem(ctk.CTkFrame):
    def __init__(self, master, file_path, on_remove, on_move_up, on_move_down):
        super().__init__(master)
        self.file_path = file_path
        
        # Estrazione numero pagine per gli slider
        doc = fitz.open(file_path)
        self.max_pagine = len(doc)
        doc.close()

        is_single = self.max_pagine <= 1
        slider_to, steps = (1.1, 1) if is_single else (self.max_pagine, self.max_pagine - 1)

        # --- Header con Nome File e Bottoni ---
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=10, pady=(5, 0))
        
        ctk.CTkLabel(self.header, text=os.path.basename(file_path), 
                     font=("Roboto", 12, "bold"), text_color="#2ecc71").pack(side="left")
        
        # Bottoni di controllo
        ctk.CTkButton(self.header, text="X", width=25, height=20, fg_color="#C0392B", 
                     hover_color="#A93226", command=lambda: on_remove(self)).pack(side="right", padx=2)
        ctk.CTkButton(self.header, text="▼", width=25, height=20, fg_color="#34495E", 
                     command=lambda: on_move_down(self)).pack(side="right", padx=2)
        ctk.CTkButton(self.header, text="▲", width=25, height=20, fg_color="#34495E", 
                     command=lambda: on_move_up(self)).pack(side="right", padx=2)

        # --- Slider Inizio (Font 13 Bold) ---
        self.label_s = ctk.CTkLabel(self, text="Inizio: 1", font=("Roboto", 13, "bold"))
        self.label_s.pack(padx=20, anchor="w", pady=(5, 0))
        self.slider_s = ctk.CTkSlider(self, from_=1, to=slider_to, number_of_steps=steps, 
                                     height=18, command=self.update_labels)
        self.slider_s.set(1)
        self.slider_s.pack(fill="x", padx=20)

        # --- Slider Fine (Font 13 Bold) ---
        self.label_e = ctk.CTkLabel(self, text=f"Fine: {self.max_pagine}", font=("Roboto", 13, "bold"))
        self.label_e.pack(padx=20, anchor="w", pady=(5, 0))
        self.slider_e = ctk.CTkSlider(self, from_=1, to=slider_to, number_of_steps=steps, 
                                     height=18, command=self.update_labels)
        self.slider_e.set(self.max_pagine)
        self.slider_e.pack(fill="x", padx=20, pady=(0, 10))

        if is_single:
            self.slider_s.configure(state="disabled")
            self.slider_e.configure(state="disabled")

    def update_labels(self, _=None):
        s, e = int(self.slider_s.get()), int(self.slider_e.get())
        s, e = min(s, self.max_pagine), min(e, self.max_pagine)
        if s > e: 
            self.slider_s.set(e)
            s = e
        self.label_s.configure(text=f"Inizio: {s}")
        self.label_e.configure(text=f"Fine: {e}")

    def get_data(self):
        return {
            "path": self.file_path, 
            "start": int(min(self.slider_s.get(), self.max_pagine)) - 1, 
            "end": int(min(self.slider_e.get(), self.max_pagine))
        }

class PDFPageMergerGUI(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self._inizializza_tkdnd()
        
        self.title("PDF Page Merger")
        self.geometry("700x650")
        
        self.items = []
        self.crea_widget()
        
        # Attivazione scroll rotella su tutta la finestra
        self._bind_mouse_wheel(self)

    def _inizializza_tkdnd(self):
        try:
            import tkinterdnd2
            path = os.path.join(os.path.dirname(tkinterdnd2.__file__), 'tkdnd', 
                                "win-x64" if sys.maxsize > 2**32 else "win-x86")
            self.tk.call('lappend', 'auto_path', path)
            self.tk.call('package', 'require', 'tkdnd')
        except:
            pass

    def _bind_mouse_wheel(self, widget):
        """Associa lo scroll evitando i widget che non supportano .bind() standard."""
        try:
            widget.bind("<MouseWheel>", self._on_mouse_wheel)
            widget.bind("<Button-4>", self._on_mouse_wheel)
            widget.bind("<Button-5>", self._on_mouse_wheel)
        except (NotImplementedError, Exception):
            pass
        
        for child in widget.winfo_children():
            self._bind_mouse_wheel(child)

    def _on_mouse_wheel(self, event):
        if not hasattr(self, 'scroll_frame') or not self.items:
            return
        delta = event.delta if event.delta != 0 else (120 if event.num == 4 else -120)
        if delta > 0:
            self.scroll_frame._parent_canvas.yview_scroll(-1, "units")
        else:
            self.scroll_frame._parent_canvas.yview_scroll(1, "units")

    def crea_widget(self):
        ctk.CTkLabel(self, text="📚 PDF Page Merger", font=("Roboto", 22, "bold")).pack(pady=15)
        
        self.style_var = ctk.StringVar(value="Orientale")
        ctk.CTkSegmentedButton(self, values=["Orientale", "Occidentale"], 
                               variable=self.style_var).pack(pady=5)

        self.drop_frame = ctk.CTkFrame(self, height=80, border_width=2, border_color="#3b8ed0")
        self.drop_frame.pack(pady=10, padx=20, fill="x")
        self.drop_frame.pack_propagate(False)
        
        ctk.CTkLabel(self.drop_frame, text="Trascina qui i PDF").pack(expand=True)
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.gestisci_drop)

        ctk.CTkButton(self, text="📁 Seleziona File", command=self.seleziona_file, 
                     fg_color="#1b5e20", hover_color="#145A32", height=32).pack(pady=5)
        
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Lista Documenti")
        
        self.progress_bar = ctk.CTkProgressBar(self)
        self.btn_avvia = ctk.CTkButton(self, text="MERGE PDF", command=self.esegui, 
                                      state="disabled", font=("Roboto", 14, "bold"), height=40)
        self.btn_avvia.pack(pady=15, side="bottom")

    def seleziona_file(self):
        paths = ctk.filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
        if paths: 
            for p in paths: self.aggiungi_pdf(p)

    def gestisci_drop(self, event):
        paths = event.data.strip('{}').split('} {')
        for p in paths:
            if p.lower().endswith('.pdf'): self.aggiungi_pdf(p)

    def aggiungi_pdf(self, path):
        if not self.items: 
            self.scroll_frame.pack(pady=5, padx=20, fill="both", expand=True, before=self.btn_avvia)
        
        item = PDFItem(self.scroll_frame, path, self.rimuovi_pdf, self.muovi_su, self.muovi_giu)
        item.pack(fill="x", pady=5, padx=5)
        self.items.append(item)
        
        self._bind_mouse_wheel(item) # Applica scroll ai nuovi widget
        self.btn_avvia.configure(state="normal")

    def rimuovi_pdf(self, item):
        item.destroy()
        self.items.remove(item)
        if not self.items: 
            self.scroll_frame.pack_forget()
            self.btn_avvia.configure(state="disabled")

    def muovi_su(self, item):
        idx = self.items.index(item)
        if idx > 0: 
            self.items[idx], self.items[idx-1] = self.items[idx-1], self.items[idx]
            self.refresh_list()

    def muovi_giu(self, item):
        idx = self.items.index(item)
        if idx < len(self.items) - 1: 
            self.items[idx], self.items[idx+1] = self.items[idx+1], self.items[idx]
            self.refresh_list()

    def refresh_list(self):
        for item in self.items: 
            item.pack_forget()
            item.pack(fill="x", pady=5, padx=5)

    def esegui(self):
        self.progress_bar.pack(pady=10, fill="x", padx=60, before=self.btn_avvia)
        self.btn_avvia.configure(state="disabled")
        self.update()
        
        tasks = [item.get_data() for item in self.items]
        try:
            elabora_documento(tasks, self.style_var.get() == "Orientale", self.progress_bar.set)
            CTkMessagebox(title="Successo", 
                         message="Operazione completata!\nI file sono nella cartella Documenti/pdf-page-merger", 
                         icon="check")
        except Exception as e: 
            CTkMessagebox(title="Errore", message=str(e), icon="cancel")
        finally: 
            self.progress_bar.pack_forget()
            self.btn_avvia.configure(state="normal")
            
class ExclusionDialog(ctk.CTkToplevel):
    def __init__(self, master, current_exclusions, max_pagine):
        super().__init__(master)
        self.title("Escludi Pagine")
        self.geometry("400x250")
        self.max_pagine = max_pagine
        self.result = current_exclusions
        
        self.label = ctk.CTkLabel(self, text="Inserisci pagine o intervalli da ESCLUDERE\n(es: 1, 3-5, 10)", font=("Roboto", 13))
        self.label.pack(pady=20)
        
        self.entry = ctk.CTkEntry(self, width=300)
        self.entry.insert(0, current_exclusions)
        self.entry.pack(pady=10)
        
        self.btn_confirm = ctk.CTkButton(self, text="Conferma", command=self.confirm)
        self.btn_confirm.pack(pady=20)
        
        self.transient(master)
        self.grab_set()

    def confirm(self):
        self.result = self.entry.get()
        self.destroy()

class PDFItem(ctk.CTkFrame):
    def __init__(self, master, file_path, on_remove, on_move_up, on_move_down):
        super().__init__(master)
        self.file_path = file_path
        self.exclusions = "" # Stringa salvata per l'utente
        
        doc = fitz.open(file_path)
        self.max_pagine = len(doc)
        doc.close()

        is_single = self.max_pagine <= 1
        slider_to, steps = (1.1, 1) if is_single else (self.max_pagine, self.max_pagine - 1)

        # --- Header ---
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=10, pady=(5, 0))
        
        ctk.CTkLabel(self.header, text=os.path.basename(file_path), 
                     font=("Roboto", 12, "bold"), text_color="#2ecc71").pack(side="left")
        
        # Bottoni
        ctk.CTkButton(self.header, text="X", width=25, height=20, fg_color="#C0392B", command=lambda: on_remove(self)).pack(side="right", padx=2)
        ctk.CTkButton(self.header, text="▼", width=25, height=20, fg_color="#34495E", command=lambda: on_move_down(self)).pack(side="right", padx=2)
        ctk.CTkButton(self.header, text="▲", width=25, height=20, fg_color="#34495E", command=lambda: on_move_up(self)).pack(side="right", padx=2)
        
        # Tasto tre puntini per esclusioni
        self.btn_dots = ctk.CTkButton(self.header, text="...", width=30, height=20, fg_color="#5D6D7E", command=self.open_exclusion_dialog)
        self.btn_dots.pack(side="right", padx=5)

        # --- Slider ---
        self.label_s = ctk.CTkLabel(self, text="Inizio: 1", font=("Roboto", 13, "bold"))
        self.label_s.pack(padx=20, anchor="w")
        self.slider_s = ctk.CTkSlider(self, from_=1, to=slider_to, number_of_steps=steps, height=18, command=self.update_labels)
        self.slider_s.set(1); self.slider_s.pack(fill="x", padx=20)

        self.label_e = ctk.CTkLabel(self, text=f"Fine: {self.max_pagine}", font=("Roboto", 13, "bold"))
        self.label_e.pack(padx=20, anchor="w")
        self.slider_e = ctk.CTkSlider(self, from_=1, to=slider_to, number_of_steps=steps, height=18, command=self.update_labels)
        self.slider_e.set(self.max_pagine); self.slider_e.pack(fill="x", padx=20, pady=(0, 10))

        if is_single:
            self.slider_s.configure(state="disabled"); self.slider_e.configure(state="disabled")

    def open_exclusion_dialog(self):
        dialog = ExclusionDialog(self.winfo_toplevel(), self.exclusions, self.max_pagine)
        self.master.wait_window(dialog)
        self.exclusions = dialog.result
        if self.exclusions.strip():
            self.btn_dots.configure(fg_color="#F39C12") # Cambia colore se ci sono esclusioni
        else:
            self.btn_dots.configure(fg_color="#5D6D7E")

    def parse_exclusions(self):
        """Converte la stringa '1, 3-5' in un set di indici (0-based)."""
        excluded_indices = set()
        parts = re.split(r'[,\s]+', self.exclusions)
        for part in parts:
            if '-' in part:
                try:
                    start, end = map(int, part.split('-'))
                    excluded_indices.update(range(start-1, end))
                except: pass
            elif part.isdigit():
                excluded_indices.add(int(part)-1)
        return excluded_indices

    def update_labels(self, _=None):
        s, e = int(self.slider_s.get()), int(self.slider_e.get())
        if s > e: self.slider_s.set(e); s = e
        self.label_s.configure(text=f"Inizio: {s}"); self.label_e.configure(text=f"Fine: {e}")

    def get_data(self):
        return {
            "path": self.file_path, 
            "start": int(self.slider_s.get()) - 1, 
            "end": int(self.slider_e.get()),
            "exclude": self.parse_exclusions()
        }