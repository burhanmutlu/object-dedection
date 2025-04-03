import cv2
import numpy as np  
import sqlite3
from datetime import datetime
import os

# Keep track of objects detected in current session
detected_objects = set()

def create_table():
    conn = sqlite3.connect('nesneler.db')
    cursor = conn.cursor()
    # Drop existing table if it exists
    cursor.execute("DROP TABLE IF EXISTS nesneler")
    # Create new table with image column
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

def clear_table():
    conn = sqlite3.connect('nesneler.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM nesneler")
    conn.commit()
    conn.close()
    print("Veritabanı temizlendi.")

def add_nesne(nesne_adi, nesne_resmi):
    # Only add if not already detected in this session
    if nesne_adi not in detected_objects:
        conn = sqlite3.connect('nesneler.db')
        cursor = conn.cursor()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Convert image to binary
        _, img_encoded = cv2.imencode('.jpg', nesne_resmi)
        img_binary = img_encoded.tobytes()
        
        cursor.execute("INSERT INTO nesneler (nesne_adi, kayit_tarihi, nesne_resmi) VALUES (?, ?, ?)", 
                      (nesne_adi, current_time, img_binary))
        conn.commit()
        conn.close()
        # Add to detected objects set
        detected_objects.add(nesne_adi)
        print(f"Yeni nesne kaydedildi: {nesne_adi}")

def view_saved_objects():
    conn = sqlite3.connect('nesneler.db')
    cursor = conn.cursor()
    cursor.execute("SELECT nesne_adi, kayit_tarihi, nesne_resmi FROM nesneler")
    rows = cursor.fetchall()
    
    for row in rows:
        nesne_adi, kayit_tarihi, img_binary = row
        # Convert binary to image
        nparr = np.frombuffer(img_binary, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Display image
        cv2.imshow(f"{nesne_adi} - {kayit_tarihi}", img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    conn.close()

# Create database table if it doesn't exist and clear it
create_table()
clear_table()

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("The camera could not be opened.")
    exit()

net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")

# net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
# net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA_FP16)

classes = []
with open("coco.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]

layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

colors = np.random.uniform(0, 255, size=(len(classes), 3))

frameCount = 0

while True:
    ret, frame = cap.read()
    frameCount += 1
    if not ret:
        break

    if frameCount % 20 == 0:
        img = frame
        img = cv2.resize(img, None, fx=0.4, fy=0.4)
        height, width, channels = img.shape

        # Detecting objects
        blob = cv2.dnn.blobFromImage(img, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
        net.setInput(blob)
        outs = net.forward(output_layers)

        class_ids = []
        confidences = []
        boxes = []
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.5:
                    # Object detected
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)

                    # Rectangle coordinates
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)

                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)

        indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

        font = cv2.FONT_HERSHEY_PLAIN
        for i in range(len(boxes)):
            if i in indexes:
                x, y, w, h = boxes[i]
                label = str(classes[class_ids[i]])
                color = colors[i]
                cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
                cv2.putText(img, label, (x, y + 30), font, 1, color, 2)
                
                # Save the object with its bounding box
                # Get the original frame coordinates (since img is resized)
                original_x = int(x / 0.4)  # 0.4 is the resize factor
                original_y = int(y / 0.4)
                original_w = int(w / 0.4)
                original_h = int(h / 0.4)
                
                # Add some padding around the object
                padding = 20
                original_x = max(0, original_x - padding)
                original_y = max(0, original_y - padding)
                original_w = min(frame.shape[1] - original_x, original_w + 2*padding)
                original_h = min(frame.shape[0] - original_y, original_h + 2*padding)
                
                # Crop the object with its surroundings
                nesne_resmi = frame[original_y:original_y+original_h, original_x:original_x+original_w]
                add_nesne(label, nesne_resmi)

        cv2.imshow("Image", img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        elif cv2.waitKey(1) & 0xFF == ord('v'):  # Press 'v' to view saved objects
            view_saved_objects()

cap.release()
cv2.destroyAllWindows()  