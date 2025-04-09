import tkinter as tk
import subprocess
import sqlite3
from tkinter import ttk
import cv2
import numpy as np
from PIL import Image, ImageTk
from tkinter import messagebox

class NesneTanimaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerçek Zamanlı Nesne Tanıma Sistemi")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        self.root.configure(bg="#f0f0f0")
        self.search_window = None

        self.style = ttk.Style()
        self.style.configure("TButton", 
                           padding=10, 
                           font=("Helvetica", 12),
                           background="#4CAF50",
                           foreground="white")
        self.style.configure("TLabel", 
                           font=("Helvetica", 12),
                           background="#f0f0f0")
        self.style.configure("Treeview",
                           font=("Helvetica", 11),
                           background="white",
                           fieldbackground="white")
        self.style.configure("Treeview.Heading",
                           font=("Helvetica", 12, "bold"),
                           background="#4CAF50",
                           foreground="white")

        self.create_widgets()

    def create_widgets(self):
        self.main_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.title_label = tk.Label(
            self.main_frame,
            text="NESNE TANIMA SİSTEMİ",
            font=("Helvetica", 24, "bold"),
            bg="#f0f0f0",
            fg="#333333"
        )
        self.title_label.pack(pady=(0, 30))

        self.button_frame = tk.Frame(self.main_frame, bg="#f0f0f0")
        self.button_frame.pack(fill=tk.X, padx=50, pady=20)

        self.camera_button = tk.Button(
            self.button_frame,
            text="Canlı Kamera Başlat",
            command=self.canli_kamera,
            font=("Helvetica", 12),
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=10,
            relief=tk.FLAT,
            cursor="hand2"
        )
        self.camera_button.pack(fill=tk.X, pady=10)

        self.search_button = tk.Button(
            self.button_frame,
            text="Kaydedilen Nesneler",
            command=self.veritabaninda_nesne_ara,
            font=("Helvetica", 12),
            bg="#2196F3",
            fg="white",
            padx=20,
            pady=10,
            relief=tk.FLAT,
            cursor="hand2"
        )
        self.search_button.pack(fill=tk.X, pady=10)

    def canli_kamera(self):
        try:
            subprocess.Popen(['python', 'canli_kamera.py'])
        except Exception as e:
            messagebox.showerror("Hata", "Kamera başlatılırken bir hata oluştu!")

    def veritabaninda_nesne_ara(self):
        if self.search_window is not None and self.search_window.winfo_exists():
            self.search_window.lift()
            return

        self.search_window = tk.Toplevel(self.root)
        self.search_window.title("Kaydedilen Nesneler")
        self.search_window.geometry("1000x700")
        self.search_window.minsize(1000, 700)
        self.search_window.configure(bg="#f0f0f0")
        
        self.search_window.protocol("WM_DELETE_WINDOW", self.on_search_window_close)

        main_frame = tk.Frame(self.search_window, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        search_frame = tk.Frame(main_frame, bg="#f0f0f0")
        search_frame.pack(fill=tk.X, pady=(0, 20))

        tk.Label(
            search_frame,
            text="Nesne Adı:",
            font=("Helvetica", 12),
            bg="#f0f0f0"
        ).pack(side=tk.LEFT, padx=10)

        search_entry = tk.Entry(
            search_frame,
            font=("Helvetica", 12),
            width=30
        )
        search_entry.pack(side=tk.LEFT, padx=10)
        search_entry.bind('<KeyRelease>', lambda event: self.search_objects(tree, search_entry))

        search_button = tk.Button(
            search_frame,
            text="Ara",
            command=lambda: self.search_objects(tree, search_entry),
            font=("Helvetica", 12),
            bg="#4CAF50",
            fg="white",
            padx=15,
            pady=5,
            relief=tk.FLAT,
            cursor="hand2"
        )
        search_button.pack(side=tk.LEFT, padx=10)

        reset_button = tk.Button(
            search_frame,
            text="Veritabanını Sıfırla",
            command=lambda: self.reset_database(tree),
            font=("Helvetica", 12),
            bg="#f44336",
            fg="white",
            padx=15,
            pady=5,
            relief=tk.FLAT,
            cursor="hand2"
        )
        reset_button.pack(side=tk.LEFT, padx=10)

        content_frame = tk.Frame(main_frame, bg="#f0f0f0")
        content_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = tk.Frame(content_frame, bg="#f0f0f0")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))

        tree = ttk.Treeview(
            left_frame,
            columns=("ID", "Nesne Adı", "Kayıt Tarihi"),
            show="headings"
        )
        tree.heading("ID", text="ID")
        tree.heading("Nesne Adı", text="Nesne Adı")
        tree.heading("Kayıt Tarihi", text="Kayıt Tarihi")
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        right_frame = tk.Frame(content_frame, bg="#f0f0f0")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        image_label = tk.Label(right_frame, bg="#f0f0f0")
        image_label.pack(pady=20)

        tree.bind('<<TreeviewSelect>>', lambda event: self.show_image(event, tree, image_label))

        self.search_objects(tree, search_entry)

    def search_objects(self, tree, search_entry):
        for item in tree.get_children():
            tree.delete(item)

        search_term = search_entry.get().lower()

        conn = sqlite3.connect('nesneler.db')
        cursor = conn.cursor()
        
        if search_term:
            cursor.execute("SELECT id, nesne_adi, kayit_tarihi FROM nesneler WHERE LOWER(nesne_adi) LIKE ?", (f'%{search_term}%',))
        else:
            cursor.execute("SELECT id, nesne_adi, kayit_tarihi FROM nesneler")
        
        results = cursor.fetchall()
        conn.close()

        if search_term and not results:
            messagebox.showwarning("Uyarı", f"'{search_term}' ile eşleşen nesne bulunamadı!")
        else:
            for result in results:
                tree.insert("", tk.END, values=result)

    def show_image(self, event, tree, image_label):
        selected_item = tree.selection()
        if not selected_item:
            return
            
        item = tree.item(selected_item[0])
        item_id = item['values'][0]

        conn = sqlite3.connect('nesneler.db')
        cursor = conn.cursor()
        cursor.execute("SELECT nesne_resmi FROM nesneler WHERE id = ?", (item_id,))
        img_binary = cursor.fetchone()[0]
        conn.close()

        nparr = np.frombuffer(img_binary, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        img = Image.fromarray(img)
        
        img = img.resize((300, 300), Image.Resampling.LANCZOS)
        
        photo = ImageTk.PhotoImage(img)
        
        image_label.configure(image=photo)
        image_label.image = photo

    def reset_database(self, tree=None):
        if self.search_window:
            self.search_window.lift()
            
        if messagebox.askyesno("Onay", "Tüm veritabanı kayıtları silinecek. Emin misiniz?"):
            try:
                conn = sqlite3.connect('nesneler.db')
                cursor = conn.cursor()
                
                cursor.execute("DROP TABLE IF EXISTS nesneler")
                cursor.execute('''
                    CREATE TABLE nesneler (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nesne_adi TEXT,
                        kayit_tarihi TEXT,
                        nesne_resmi BLOB
                    )
                ''')
                conn.commit()
                conn.close()
                
                if tree:
                    for item in tree.get_children():
                        tree.delete(item)
                
                if self.search_window:
                    self.search_window.lift()
                messagebox.showinfo("Başarılı", "Veritabanı başarıyla sıfırlandı!")
                if self.search_window:
                    self.search_window.lift()
            except Exception as e:
                if self.search_window:
                    self.search_window.lift()
                messagebox.showerror("Hata", "Veritabanı sıfırlanırken bir hata oluştu!")
                if self.search_window:
                    self.search_window.lift()

    def on_search_window_close(self):
        self.search_window.destroy()
        self.search_window = None

if __name__ == "__main__":
    root = tk.Tk()
    app = NesneTanimaApp(root)
    root.mainloop()

