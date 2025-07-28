import cv2
import numpy as np
import mss
import time
import torch_directml
from ultralytics import YOLO

# ========================
# KONFIGURASI
# ========================
# Area capture layar (ubah sesuai posisi window ATCS)
CAPTURE_REGION = {"top": 100, "left": 100, "width": 800, "height": 600}

# Model YOLO (gunakan yang lebih ringan dulu, contoh: yolo11s)
MODEL_PATH = "yolo-Weights/yolo11s.pt"
TARGET_CLASSES = [2, 3, 5, 7]  # car, motorcycle, bus, truck
CONFIDENCE_THRESHOLD = 0.25

# ========================
# INIT YOLO DAN DEVICE
# ========================
print("Loading YOLO model...")
device = torch_directml.device()   # Gunakan GPU AMD via DirectML
model = YOLO(MODEL_PATH)
model.to(device)
print(f"Model loaded to DirectML device: {device}")

sct = mss.mss()

# ========================
# LOOP
# ========================
prev_time = time.time()
fps = 0

while True:
    # Capture layar
    screenshot = sct.grab(CAPTURE_REGION)
    frame = np.array(screenshot)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

    # Resize agar YOLO lebih cepat
    frame_resized = cv2.resize(frame, (480, 270))

    # Deteksi + Tracking
    results = model.track(frame_resized, 
                          persist=True, 
                          conf=CONFIDENCE_THRESHOLD, 
                          classes=TARGET_CLASSES, 
                          max_det=50)

    # Ambil hasil dengan bounding box
    annotated = results[0].plot()

    # Hitung FPS
    current_time = time.time()
    fps = 1 / (current_time - prev_time)
    prev_time = current_time
    cv2.putText(annotated, f"FPS: {fps:.2f}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Tampilkan
    cv2.imshow("Deteksi Kendaraan ATCS (DirectML Optimized)", annotated)

    # Exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
