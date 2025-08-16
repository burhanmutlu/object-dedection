import tkinter as tk  # GUI oluşturmak için tkinter kütüphanesi
import subprocess    # Alt işlemleri başlatmak için subprocess kütüphanesi
import sqlite3      # Veritabanı işlemleri için sqlite3 kütüphanesi
from tkinter import ttk  # Tkinter'ın modern widget'ları için ttk modülü
import cv2          # Görüntü işleme için OpenCV kütüphanesi
import numpy as np  # Sayısal işlemler için numpy kütüphanesi
from PIL import Image, ImageTk  # Görüntü işleme için PIL kütüphanesi
from tkinter import messagebox  # Mesaj kutuları için messagebox modülü

class NesneTanimaApp:
    def __init__(self, root):
        # Ana pencere ayarları
        self.root = root  # Ana pencere referansı
        self.root.title("Gerçek Zamanlı Nesne Tanıma Sistemi")  # Pencere başlığı
        self.root.geometry("1000x800")  # Pencere boyutu (genişlik x yükseklik)
        self.root.minsize(1000, 800)    # Minimum pencere boyutu (küçültülemez)
        self.root.configure(bg="#f0f0f0")  # Arka plan rengi (açık gri)
        self.search_window = None  # Arama penceresi referansı (başlangıçta boş)
        self.selected_objects = set()  # Seçili nesneleri tutan küme (başlangıçta boş)

        # COCO nesnelerinin Türkçe çevirileri
        self.turkish_translations = {
            'person': 'kişi',
            'bicycle': 'bisiklet',
            'car': 'araba',
            'motorbike': 'motosiklet',
            'aeroplane': 'uçak',
            'bus': 'otobüs',
            'train': 'tren',
            'truck': 'kamyon',
            'boat': 'tekne',
            'traffic light': 'trafik ışığı',
            'fire hydrant': 'yangın musluğu',
            'stop sign': 'dur işareti',
            'parking meter': 'parkmetre',
            'bench': 'bank',
            'bird': 'kuş',
            'cat': 'kedi',
            'dog': 'köpek',
            'horse': 'at',
            'sheep': 'koyun',
            'cow': 'inek',
            'elephant': 'fil',
            'bear': 'ayı',
            'zebra': 'zebra',
            'giraffe': 'zürafa',
            'backpack': 'sırt çantası',
            'umbrella': 'şemsiye',
            'handbag': 'el çantası',
            'tie': 'kravat',
            'suitcase': 'bavul',
            'frisbee': 'frizbi',
            'skis': 'kayak',
            'snowboard': 'snowboard',
            'sports ball': 'spor topu',
            'kite': 'uçurtma',
            'baseball bat': 'beyzbol sopası',
            'baseball glove': 'beyzbol eldiveni',
            'skateboard': 'kaykay',
            'surfboard': 'sörf tahtası',
            'tennis racket': 'tenis raketi',
            'bottle': 'şişe',
            'wine glass': 'şarap bardağı',
            'cup': 'fincan',
            'fork': 'çatal',
            'knife': 'bıçak',
            'spoon': 'kaşık',
            'bowl': 'kase',
            'banana': 'muz',
            'apple': 'elma',
            'sandwich': 'sandviç',
            'orange': 'portakal',
            'broccoli': 'brokoli',
            'carrot': 'havuç',
            'hot dog': 'hot dog',
            'pizza': 'pizza',
            'donut': 'donut',
            'cake': 'pasta',
            'chair': 'sandalye',
            'sofa': 'kanepe',
            'pottedplant': 'saksı bitkisi',
            'bed': 'yatak',
            'diningtable': 'yemek masası',
            'toilet': 'tuvalet',
            'tvmonitor': 'tv monitör',
            'laptop': 'dizüstü bilgisayar',
            'mouse': 'fare',
            'remote': 'kumanda',
            'keyboard': 'klavye',
            'cell phone': 'cep telefonu',
            'microwave': 'mikrodalga',
            'oven': 'fırın',
            'toaster': 'tost makinesi',
            'sink': 'lavabo',
            'refrigerator': 'buzdolabı',
            'book': 'kitap',
            'clock': 'saat',
            'vase': 'vazo',
            'scissors': 'makas',
            'teddy bear': 'oyuncak ayı',
            'hair drier': 'saç kurutma makinesi',
            'toothbrush': 'diş fırçası'
        }

        # coco.names dosyasından nesne isimleri okunur
        with open('coco.names', 'r') as f:
            self.coco_names = [line.strip() for line in f.readlines()]

        self.style = ttk.Style()
        # Buton stili
        self.style.configure("TButton", 
                           padding=10,  # İç boşluk
                           font=("Helvetica", 12),  # Yazı tipi ve boyutu
                           background="#4CAF50",  # Arka plan rengi (yeşil)
                           foreground="white")  # Yazı rengi (beyaz)
        # Etiket stili
        self.style.configure("TLabel", 
                           font=("Helvetica", 12),  # Yazı tipi ve boyutu
                           background="#f0f0f0")  # Arka plan rengi
        # Ağaç görünümü stili
        self.style.configure("Treeview",
                           font=("Helvetica", 11),  # Yazı tipi ve boyutu
                           background="white",  # Arka plan rengi
                           fieldbackground="white")  # Alan arka plan rengi
        # Ağaç başlık stili
        self.style.configure("Treeview.Heading",
                           font=("Helvetica", 12, "bold"),  # Kalın yazı tipi
                           background="#4CAF50",  # Arka plan rengi
                           foreground="white")  # Yazı rengi

        self.create_widgets()  # Arayüz elemanlarını oluştur

    def create_widgets(self):
        # Ana frame oluşturma (tüm içeriği kapsayan ana konteyner)
        self.main_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Başlık etiketi
        self.title_label = tk.Label(
            self.main_frame,
            text="NESNE TANIMA SİSTEMİ",
            font=("Helvetica", 24, "bold"),  # Büyük ve kalın yazı tipi
            bg="#f0f0f0",  # Arka plan rengi
            fg="#333333"   # Yazı rengi (koyu gri)
        )
        self.title_label.pack(pady=(0, 30))  # Üstten 30 piksel boşluk

        # İçerik frame'i oluşturma (sol ve sağ bölümleri içeren konteyner)
        content_frame = tk.Frame(self.main_frame, bg="#f0f0f0")
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Sol frame (nesne listesi için)
        left_frame = tk.Frame(content_frame, bg="#f0f0f0")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))

        # Kaydırma çubuğu ve canvas oluşturma
        # Uzun nesne listesi için kaydırılabilir alan
        canvas = tk.Canvas(left_frame, bg="#f0f0f0")
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        self.list_frame = tk.Frame(canvas, bg="#f0f0f0")

        canvas.configure(yscrollcommand=scrollbar.set)

        # Kaydırma çubuğu ve canvas'ı yerleştirme
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)  # Sağ tarafa dikey kaydırma çubuğu
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)  # Sol tarafa canvas

        # Canvas içinde liste frame'i oluşturma
        canvas.create_window((0, 0), window=self.list_frame, anchor="nw")

        # Her satırda 5 nesne olacak şekilde checkbox'ları oluşturma
        self.object_vars = {}  # Checkbox değişkenlerini tutan sözlük
        items_per_row = 5  # Her satırdaki nesne sayısı
        for i, obj in enumerate(self.coco_names):
            row = i // items_per_row  # Satır numarası hesaplama (tam bölme)
            col = i % items_per_row   # Sütun numarası hesaplama (kalan)
            
            var = tk.BooleanVar()  # Checkbox değişkeni (seçili/seçili değil)
            self.object_vars[obj] = var  # Değişkeni sözlüğe ekleme
            
            # Her checkbox için frame oluşturma
            checkbox_frame = tk.Frame(self.list_frame, bg="#f0f0f0")
            checkbox_frame.grid(row=row, column=col, padx=5, pady=5, sticky="w")
            
            # Türkçe ismi alma (çeviri sözlüğünden)
            turkish_name = self.turkish_translations.get(obj, obj)
            
            # Checkbox oluşturma
            cb = tk.Checkbutton(
                checkbox_frame,
                text=turkish_name,  # Türkçe nesne adı
                variable=var,  # Checkbox değişkeni
                bg="#f0f0f0",  # Arka plan rengi
                font=("Helvetica", 10),  # Yazı tipi ve boyutu
                command=self.update_selected_objects  # Seçim değiştiğinde çalışacak fonksiyon
            )
            cb.pack(anchor="w")  # Sola hizalı yerleştirme

        # Canvas kaydırma ayarları
        # Liste boyutu değiştiğinde kaydırma alanını güncelle
        self.list_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        # Canvas boyutu değiştiğinde içerik genişliğini güncelle
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas.find_all()[0], width=e.width))

        # Sağ frame (butonlar için)
        right_frame = tk.Frame(content_frame, bg="#f0f0f0")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(20, 0))

        # Kamera başlatma butonu
        self.camera_button = tk.Button(
            right_frame,
            text="Canlı Kamera Başlat",
            command=self.canli_kamera,  # Tıklandığında çalışacak fonksiyon
            font=("Helvetica", 12),  # Yazı tipi ve boyutu
            bg="#4CAF50",  # Arka plan rengi (yeşil)
            fg="white",  # Yazı rengi (beyaz)
            padx=20,  # Yatay iç boşluk
            pady=10,  # Dikey iç boşluk
            relief=tk.FLAT,  # Düz görünüm
            cursor="hand2"  # El işaretçisi
        )
        self.camera_button.pack(fill=tk.X, pady=10)  # Yatay doldurma ve dikey boşluk

        # Kaydedilen nesneler butonu
        self.search_button = tk.Button(
            right_frame,
            text="Kaydedilen Nesneler",
            command=self.veritabaninda_nesne_ara,  # Tıklandığında çalışacak fonksiyon
            font=("Helvetica", 12),  # Yazı tipi ve boyutu
            bg="#2196F3",  # Arka plan rengi (mavi)
            fg="white",  # Yazı rengi (beyaz)
            padx=20,  # Yatay iç boşluk
            pady=10,  # Dikey iç boşluk
            relief=tk.FLAT,  # Düz görünüm
            cursor="hand2"  # El işaretçisi
        )
        self.search_button.pack(fill=tk.X, pady=10)  # Yatay doldurma ve dikey boşluk

    def update_selected_objects(self):
        # Seçili nesneleri güncelleme (işaretli olanları seç)
        self.selected_objects = {obj for obj, var in self.object_vars.items() if var.get()}

    def canli_kamera(self):
        try:
            # Seçili nesne kontrolü
            if not self.selected_objects:
                messagebox.showwarning("Uyarı", "Lütfen en az bir nesne seçin!")
                return
            # Kamera scriptini başlatma ve seçili nesneleri iletme
            subprocess.Popen(['python', 'canli_kamera.py', ','.join(self.selected_objects)])
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

