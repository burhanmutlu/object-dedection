import tkinter as tk

root = tk.Tk()

root.title("Gerçek Zamanlı Nesne Tanıma")
root.geometry("400x400")

label = tk.Label(root, text="Merhaba, Tkinter!", font=("Arial", 14))
label.pack(pady=20)# İki buton ekleme
def canli_kamera():
    label.config(text="Canlı Kamera Açılıyor...")

def veritabaninda_nesne_ara():
    label.config(text="Veritabanında Nesne Aranıyor...")

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