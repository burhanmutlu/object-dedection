import cv2          # Görüntü işleme için OpenCV kütüphanesi
import numpy as np  # Sayısal işlemler için numpy kütüphanesi
import sqlite3      # Veritabanı işlemleri için sqlite3 kütüphanesi
from datetime import datetime  # Tarih ve zaman işlemleri için datetime modülü
import os          # Dosya sistemi işlemleri için os modülü
import sys         # Sistem işlemleri için sys modülü

# Tespit edilen nesneleri tutan küme
detected_objects = set()

def create_table():
    # Veritabanı bağlantısı oluşturma
    conn = sqlite3.connect('nesneler.db')
    cursor = conn.cursor()
    
    # Tablonun var olup olmadığını kontrol etme
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='nesneler'")
    table_exists = cursor.fetchone() is not None
    
    # Tablo yoksa oluşturma
    if not table_exists:
        cursor.execute('''
            CREATE TABLE nesneler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nesne_adi TEXT,
                kayit_tarihi TEXT,
                nesne_resmi BLOB
            )
        ''')
    conn.commit()  # Değişiklikleri kaydetme
    conn.close()  # Bağlantıyı kapatma

def add_nesne(nesne_adi, nesne_resmi):
    # Veritabanı bağlantısı oluşturma
    conn = sqlite3.connect('nesneler.db')
    cursor = conn.cursor()
    
    # Şu anki zamanı alma
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Görüntüyü binary formata dönüştürme
    _, img_encoded = cv2.imencode('.jpg', nesne_resmi)
    img_binary = img_encoded.tobytes()
    
    # Veritabanına kaydetme
    cursor.execute("INSERT INTO nesneler (nesne_adi, kayit_tarihi, nesne_resmi) VALUES (?, ?, ?)", 
                  (nesne_adi, current_time, img_binary))
    conn.commit()  # Değişiklikleri kaydetme
    print(f"Yeni nesne kaydedildi: {nesne_adi}")
    
    conn.close()  # Bağlantıyı kapatma

def display_saved_objects():
    # Veritabanı bağlantısı oluşturma
    conn = sqlite3.connect('nesneler.db')
    cursor = conn.cursor()
    cursor.execute("SELECT nesne_adi, kayit_tarihi, nesne_resmi FROM nesneler")
    rows = cursor.fetchall()
    
    # Her kaydedilen nesneyi gösterme
    for row in rows:
        nesne_adi, kayit_tarihi, img_binary = row
        # Binary görüntüyü numpy dizisine dönüştürme
        nparr = np.frombuffer(img_binary, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Görüntüyü gösterme
        cv2.imshow(f"{nesne_adi} - {kayit_tarihi}", img)
        cv2.waitKey(0)  # Tuş basılana kadar bekleme
        cv2.destroyAllWindows()  # Tüm pencereleri kapatma
    
    conn.close()  # Bağlantıyı kapatma

# Veritabanı tablosunu oluşturma
create_table()

# Komut satırı argümanlarından seçili nesneleri alma
selected_objects = set()  # Seçili nesneleri tutan küme
if len(sys.argv) > 1:  # Eğer argüman varsa
    selected_objects = set(sys.argv[1].split(','))  # Virgülle ayrılmış nesneleri küme olarak alma

# Kamerayı başlatma
cap = cv2.VideoCapture(0)  # Varsayılan kamerayı açma

# Kamera açılamazsa hata verme
if not cap.isOpened():
    print("Kamera açılırken hata oluştu.")
    exit()

# YOLO modelini yükleme
net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")  # YOLO modelini yükleme

# COCO sınıf isimlerini yükleme
classes = []  # Sınıf isimlerini tutan liste
with open("coco.names", "r") as f:  # coco.names dosyasını okuma
    classes = [line.strip() for line in f.readlines()]  # Her satırı temizleyerek listeye ekleme

# YOLO katmanlarını alma
layer_names = net.getLayerNames()  # Tüm katman isimlerini alma
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]  # Çıkış katmanlarını alma

# Her sınıf için rastgele renk oluşturma
colors = np.random.uniform(0, 255, size=(len(classes), 3))  # Her sınıf için RGB renk değerleri

# Kare sayacı
frameCount = 0  # İşlenen kare sayısı

# Ana döngü
while True:
    # Kameradan kare alma
    ret, frame = cap.read()  # Bir kare okuma
    if not ret:  # Kare okunamazsa döngüyü sonlandır
        break

    # Görüntüyü yeniden boyutlandırma
    img = frame  # Orijinal kareyi kopyalama
    img = cv2.resize(img, None, fx=0.4, fy=0.4)  # Görüntüyü %40 oranında küçültme
    height, width, channels = img.shape  # Görüntü boyutlarını alma

    # Görüntüyü YOLO formatına dönüştürme
    blob = cv2.dnn.blobFromImage(img, 0.00392, (416, 416), (0, 0, 0), True, crop=False)  # Görüntüyü blob formatına dönüştürme
    net.setInput(blob)  # Blob'u modele girdi olarak verme
    outs = net.forward(output_layers)  # İleri yayılım yapma

    # Tespit sonuçlarını tutacak listeler
    class_ids = []  # Sınıf ID'lerini tutan liste
    confidences = []  # Güven değerlerini tutan liste
    boxes = []  # Kutu koordinatlarını tutan liste

    # Tespitleri işleme
    for out in outs:  # Her çıkış katmanı için
        for detection in out:  # Her tespit için
            scores = detection[5:]  # Sınıf skorlarını alma
            class_id = np.argmax(scores)  # En yüksek skora sahip sınıfın ID'sini alma
            confidence = scores[class_id]  # Güven değerini alma
            if confidence > 0.5:  # Güven değeri 0.5'ten büyükse
                # Sadece seçili nesneleri işleme
                if not selected_objects or classes[class_id] in selected_objects:
                    # Nesne konumunu hesaplama
                    center_x = int(detection[0] * width)  # Merkez x koordinatı
                    center_y = int(detection[1] * height)  # Merkez y koordinatı
                    w = int(detection[2] * width)  # Genişlik
                    h = int(detection[3] * height)  # Yükseklik

                    x = int(center_x - w / 2)  # Sol üst köşe x koordinatı
                    y = int(center_y - h / 2)  # Sol üst köşe y koordinatı

                    boxes.append([x, y, w, h])  # Kutu koordinatlarını listeye ekleme
                    confidences.append(float(confidence))  # Güven değerini listeye ekleme
                    class_ids.append(class_id)  # Sınıf ID'sini listeye ekleme

    # Çakışan kutuları filtreleme
    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)  # Çakışan kutuları eleme

    # Tespit edilen nesneleri çizme
    font = cv2.FONT_HERSHEY_PLAIN  # Yazı tipi
    for i in range(len(boxes)):  # Her kutu için
        if i in indexes:  # Eğer kutu filtrelemeden geçtiyse
            x, y, w, h = boxes[i]  # Kutu koordinatlarını alma
            label = str(classes[class_ids[i]])  # Nesne adını alma
            color = colors[class_ids[i]]  # Nesne rengini alma
            cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)  # Kutuyu çizme
            cv2.putText(img, label, (x, y + 30), font, 1, color, 2)  # Nesne adını yazma
            
            # Orijinal görüntü boyutlarına göre koordinatları ayarlama
            original_x = int(x / 0.4)  # Orijinal x koordinatı
            original_y = int(y / 0.4)  # Orijinal y koordinatı
            original_w = int(w / 0.4)  # Orijinal genişlik
            original_h = int(h / 0.4)  # Orijinal yükseklik
            
            # Kenar boşluğu ekleme
            padding = 20  # Kenar boşluğu miktarı
            original_x = max(0, original_x - padding)  # Sol kenar boşluğu
            original_y = max(0, original_y - padding)  # Üst kenar boşluğu
            original_w = min(frame.shape[1] - original_x, original_w + 2*padding)  # Sağ kenar boşluğu
            original_h = min(frame.shape[0] - original_y, original_h + 2*padding)  # Alt kenar boşluğu
            
            # Nesne görüntüsünü kesme ve kaydetme
            nesne_resmi = frame[original_y:original_y+original_h, original_x:original_x+original_w]  # Nesneyi kesme
            add_nesne(label, nesne_resmi)  # Veritabanına kaydetme

    # Görüntüyü gösterme
    cv2.imshow("Image", img)  # İşlenmiş görüntüyü gösterme

    # Tuş kontrolleri
    if cv2.waitKey(1) & 0xFF == ord('q'):  # q tuşu ile çıkış
        break
    elif cv2.waitKey(1) & 0xFF == ord('v'):  # v tuşu ile kaydedilen nesneleri görüntüleme
        display_saved_objects()

# Kaynakları serbest bırakma
cap.release()  # Kamerayı kapatma
cv2.destroyAllWindows()  # Tüm pencereleri kapatma