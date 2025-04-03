import tkinter as tk
import subprocess
import sqlite3
from tkinter import ttk
import cv2
import numpy as np
from PIL import Image, ImageTk

root = tk.Tk()

root.title("Gerçek Zamanlı Nesne Tanıma")
root.geometry("400x400")

label = tk.Label(root, text="Merhaba, Tkinter!", font=("Arial", 14))
label.pack(pady=20)# İki buton ekleme
def canli_kamera():
    label.config(text="Canlı Kamera Açılıyor...")
    subprocess.Popen(['python', 'canli_kamera.py'])

def veritabaninda_nesne_ara():
    # Create a new window for search
    search_window = tk.Toplevel(root)
    search_window.title("Nesne Arama")
    search_window.geometry("800x600")

    # Create main frame
    main_frame = tk.Frame(search_window)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Create left frame for search and results
    left_frame = tk.Frame(main_frame)
    left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Create search frame
    search_frame = tk.Frame(left_frame)
    search_frame.pack(pady=10)

    # Search label and entry
    tk.Label(search_frame, text="Nesne Adı:").pack(side=tk.LEFT, padx=5)
    search_entry = tk.Entry(search_frame)
    search_entry.pack(side=tk.LEFT, padx=5)

    # Create treeview for results
    tree = ttk.Treeview(left_frame, columns=("ID", "Nesne Adı", "Kayıt Tarihi"), show="headings")
    tree.heading("ID", text="ID")
    tree.heading("Nesne Adı", text="Nesne Adı")
    tree.heading("Kayıt Tarihi", text="Kayıt Tarihi")
    tree.pack(pady=10, fill=tk.BOTH, expand=True)

    # Create right frame for image display
    right_frame = tk.Frame(main_frame)
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    # Image label
    image_label = tk.Label(right_frame)
    image_label.pack(pady=10)

    def show_image(event):
        selected_item = tree.selection()
        if not selected_item:
            return
            
        item = tree.item(selected_item[0])
        item_id = item['values'][0]  # Get ID from selected item

        # Connect to database and get image
        conn = sqlite3.connect('nesneler.db')
        cursor = conn.cursor()
        cursor.execute("SELECT nesne_resmi FROM nesneler WHERE id = ?", (item_id,))
        img_binary = cursor.fetchone()[0]
        conn.close()

        # Convert binary to image
        nparr = np.frombuffer(img_binary, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Convert BGR to RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        img = Image.fromarray(img)
        
        # Resize image to fit in the window
        img = img.resize((300, 300), Image.Resampling.LANCZOS)
        
        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(img)
        
        # Update image label
        image_label.configure(image=photo)
        image_label.image = photo  # Keep a reference

    def search_objects():
        # Clear previous results
        for item in tree.get_children():
            tree.delete(item)

        # Get search term
        search_term = search_entry.get().lower()

        # Connect to database and search
        conn = sqlite3.connect('nesneler.db')
        cursor = conn.cursor()
        
        if search_term:
            cursor.execute("SELECT id, nesne_adi, kayit_tarihi FROM nesneler WHERE LOWER(nesne_adi) LIKE ?", (f'%{search_term}%',))
        else:
            cursor.execute("SELECT id, nesne_adi, kayit_tarihi FROM nesneler")
        
        results = cursor.fetchall()
        conn.close()

        # Display results
        for result in results:
            tree.insert("", tk.END, values=result)

    # Bind selection event
    tree.bind('<<TreeviewSelect>>', show_image)

    # Search button
    search_button = tk.Button(search_frame, text="Ara", command=search_objects)
    search_button.pack(side=tk.LEFT, padx=5)

    # Initial search to show all objects
    search_objects()

button_canli_kamera = tk.Button(root, text="Canlı Kamera", command=canli_kamera)
button_canli_kamera.pack(pady=10)

button_veritabani = tk.Button(root, text="Veritabanında Nesne Ara", command=veritabaninda_nesne_ara)
button_veritabani.pack(pady=10)


# Buton ekleme
def tiklandi():
    label.config(text="Butona tıklandı!")

button = tk.Button(root, text="Tıkla!", command=tiklandi)
button.pack(pady=10)

# Pencereyi çalıştır
root.mainloop()

