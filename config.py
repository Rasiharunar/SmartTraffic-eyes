"""
Configuration file untuk Vehicle Counter Application
"""

# Database Configuration
DATABASE_CONFIG = {
    'dbname': "person_counter",
    'user': "magang",
    'password': "magang123#",
    'host': "10.98.33.122",
    'port': "5433"
}

# YOLO Model Configuration
MODEL_CONFIG = {
    'model_path': 'yolo11n.pt',
    'confidence_threshold': 0.05,
    'iou_threshold': 0.5,
    'detection_confidence': 0.10
}

# Vehicle Classes (COCO dataset)
VEHICLE_CLASSES = [2, 3, 5, 7]  # car, motorcycle, bus, truck
CLASS_NAMES = {2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'}

# GUI Configuration
GUI_CONFIG = {
    'window_title': "YOLO Vehicle Counter - Screen Capture v2.3 DIRECTIONAL",
    'window_size': "1400x900",
    'fps_target': 30
}

# Line Settings Default
DEFAULT_LINE_SETTINGS = {
    'line_color': '#FF0000',
    'line_thickness': 3,
    'line_style': 'solid',
    'show_label': True,
    'label_text': 'COUNTING LINE',
    'detection_threshold': 100,
    'line_type': 'manual'
}

# Tracking Configuration
TRACKING_CONFIG = {
    'max_distance': 150,
    'path_history_length': 20,
    'track_timeout': 1.5,
    'min_detection_size': 50
}

# Color Configuration untuk Bounding Box
COLOR_CONFIG = {
    'active_vehicle': (0, 255, 0),      # Hijau untuk kendaraan aktif (BGR format)
    'counted_vehicle': (128, 128, 128), # Abu-abu untuk kendaraan yang sudah dihitung
    'center_dot_active': (0, 0, 255),   # Merah untuk center dot kendaraan aktif
    'center_dot_counted': (64, 64, 64), # Abu-abu gelap untuk center dot yang sudah dihitung
    'tracking_path': (255, 0, 0),       # Biru untuk jalur tracking
    'tracking_path_counted': (64, 64, 64) # Abu-abu untuk jalur kendaraan yang sudah dihitung
}