import os
import hashlib
import subprocess
import platform
import sys
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import imagehash

# Importations optionnelles avec sécurité pour les vieilles versions
try:
    import rawpy
except ImportError: rawpy = None
try:
    import cv2
except ImportError: cv2 = None
try:
    import pydicom
    import numpy as np
except ImportError: pydicom = None

# Configuration pour éviter les crashs sur images lourdes
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

class NettoyeurUltraCompatible(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Gestion de la haute résolution (Windows/Mac)
        if platform.system() == "Windows":
            try:
                from ctypes import windll
                windll.shcore.SetProcessDpiAwareness(1)
            except: pass

        self.title("🚀 Nettoyeur Universel v2.0")
        self.geometry("1100x800")

        self.empreintes = {}
        self.vignettes_refs = []
        self.doublons_detectes = []
        self.chemin_selectionne = ""

        # Layout adaptable
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Galerie
        self.frame_gauche = ctk.CTkFrame(self)
        self.frame_gauche.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.btn_scanner = ctk.CTkButton(self.frame_gauche, text="📁 1. Sélectionner et Scanner", 
                                         command=self.lancer_scan, height=45, font=("Arial", 16, "bold"))
        self.btn_scanner.pack(pady=15)

        self.scroll_galerie = ctk.CTkScrollableFrame(self.frame_gauche, label_text="Bibliothèque Complète (Doublons en rouge)")
        self.scroll_galerie.pack(expand=True, fill="both", padx=5, pady=5)
        self.scroll_galerie.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Inspecteur
        self.frame_info = ctk.CTkFrame(self, width=300)
        self.frame_info.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.canvas_preview = ctk.CTkLabel(self.frame_info, text="Aperçu", width=280, height=280, fg_color="#1a1a1a")
        self.canvas_preview.pack(pady=20)

        self.btn_clean = ctk.CTkButton(self.frame_info, text="🔥 Supprimer TOUS les doublons", 
                                       fg_color="#D32F2F", state="disabled", command=self.nettoyer_auto)
        self.btn_clean.pack(pady=10, padx=10)

    def extraire_image(self, chemin):
        p_chemin = Path(chemin)
        ext = p_chemin.suffix.lower()
        try:
            # Vidéo
            if cv2 and ext in ['.mp4', '.mkv', '.mov', '.avi']:
                cap = cv2.VideoCapture(str(p_chemin))
                ret, frame = cap.read(); cap.release()
                if ret: return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            # Médical
            elif pydicom and ext == '.dcm':
                ds = pydicom.dcmread(str(p_chemin))
                return Image.fromarray((ds.pixel_array / ds.pixel_array.max() * 255).astype(np.uint8))
            # RAW
            elif rawpy and ext in ['.cr2', '.nef', '.arw', '.dng']:
                with rawpy.imread(str(p_chemin)) as raw:
                    thumb = raw.extract_thumb(); import io
                    return Image.open(io.BytesIO(thumb.data))
            # Standard
            return Image.open(str(p_chemin))
        except: return None

    def lancer_scan(self):
        dossier = filedialog.askdirectory()
        if not dossier: return

        for w in self.scroll_galerie.winfo_children(): w.destroy()
        self.empreintes = {}
        self.doublons_detectes = []
        self.vignettes_refs = []
        row, col = 0, 0

        p_dossier = Path(dossier)
        for p_file in p_dossier.rglob('*'): # rglob parcourt tout récursivement
            if p_file.is_file():
                chemin = str(p_file)
                img_pil = self.extraire_image(chemin)
                
                if img_pil:
                    try:
                        sig = str(imagehash.phash(img_pil.convert('RGB')))
                    except:
                        sig = hashlib.md5(p_file.read_bytes()).hexdigest()
                    
                    est_doublon = False
                    if sig in self.empreintes:
                        est_doublon = True
                        self.doublons_detectes.append(chemin)
                    else:
                        self.empreintes[sig] = chemin

                    img_pil.thumbnail((120, 120))
                    img_tk = ImageTk.PhotoImage(img_pil)
                    self.vignettes_refs.append(img_tk)

                    # Interface dynamique
                    color = "#FF4444" if est_doublon else "#2b2b2b"
                    lbl = "DOUBLON" if est_doublon else ""
                    btn = ctk.CTkButton(self.scroll_galerie, image=img_tk, text=lbl, compound="top",
                                        fg_color=color, command=lambda c=chemin: self.voir(c))
                    btn.grid(row=row, column=col, padx=5, pady=5)
                    
                    col += 1
                    if col > 3: col = 0; row += 1
                    self.update()

        if self.doublons_detectes: self.btn_clean.configure(state="normal")

    def voir(self, chemin):
        img = self.extraire_image(chemin)
        if img:
            img.thumbnail((280, 280))
            self.canvas_preview.configure(image=ctk.CTkImage(light_image=img, size=img.size), text="")

    def nettoyer_auto(self):
        if messagebox.askyesno("Nettoyage", f"Supprimer {len(self.doublons_detectes)} doublons ?"):
            for d in self.doublons_detectes:
                try: os.remove(d)
                except: pass
            messagebox.showinfo("Fini", "Nettoyage terminé !")
            self.btn_clean.configure(state="disabled")

if __name__ == "__main__":
    app = NettoyeurUltraCompatible()
    app.mainloop()
