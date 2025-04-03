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
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='nesneler'")
    table_exists = cursor.fetchone() is not None
    
    if not table_exists:
        # Create new table if it doesn't exist
        cursor.execute('''
            CREATE TABLE nesneler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nesne_adi TEXT,
                kayit_tarihi TEXT,
                nesne_resmi BLOB,
                unique_id TEXT
            )
        ''')
    else:
        # Check if unique_id column exists
        cursor.execute("PRAGMA table_info(nesneler)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'unique_id' not in columns:
            # Add unique_id column if it doesn't exist
            cursor.execute("ALTER TABLE nesneler ADD COLUMN unique_id TEXT")
    
    conn.commit()
    conn.close()

def add_nesne(nesne_adi, nesne_resmi, unique_id):
    conn = sqlite3.connect('nesneler.db')
    cursor = conn.cursor()
    
    # Check if this exact object (same name and unique_id) was already detected
    cursor.execute("SELECT COUNT(*) FROM nesneler WHERE nesne_adi = ? AND unique_id = ?", (nesne_adi, unique_id))
    count = cursor.fetchone()[0]
    
    if count == 0:  # Only add if not already detected
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Convert image to binary
        _, img_encoded = cv2.imencode('.jpg', nesne_resmi)
        img_binary = img_encoded.tobytes()
        
        cursor.execute("INSERT INTO nesneler (nesne_adi, kayit_tarihi, nesne_resmi, unique_id) VALUES (?, ?, ?, ?)", 
                      (nesne_adi, current_time, img_binary, unique_id))
        conn.commit()
        print(f"Yeni nesne kaydedildi: {nesne_adi}")
    
    conn.close()

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

# Create database table if it doesn't exist
create_table()

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
        if len(indexes) == 0:
            # Display "No objects detected" message
            text = "Nesne bulunamadı"
            text_size = cv2.getTextSize(text, font, 2, 2)[0]
            text_x = (img.shape[1] - text_size[0]) // 2
            text_y = (img.shape[0] + text_size[1]) // 2
            cv2.putText(img, text, (text_x, text_y), font, 2, (0, 0, 255), 2)
        else:
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
                    
                    # Generate a unique ID based on object position and size
                    unique_id = f"{original_x}_{original_y}_{original_w}_{original_h}"
                    add_nesne(label, nesne_resmi, unique_id)

        cv2.imshow("Image", img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        elif cv2.waitKey(1) & 0xFF == ord('v'):  # Press 'v' to view saved objects
            view_saved_objects()

cap.release()
cv2.destroyAllWindows()  