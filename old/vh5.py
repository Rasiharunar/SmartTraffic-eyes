from flask import Flask, render_template, Response, request, jsonify
import cv2
from pytube import YouTube
import numpy as np
from ultralytics import YOLO
from collections import defaultdict
import datetime
import psycopg2  # For PostgreSQL operations

app = Flask(__name__)

# Initialize YOLO model
model = YOLO('yolo11n.pt')

# Vehicle classes in COCO dataset
vehicle_classes = [2, 3, 5, 7]  # car, motorcycle, bus, truck
class_names = {2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'}

# Global variables for counting
counted_ids = set()
vehicle_count_up = defaultdict(int)
vehicle_count_down = defaultdict(int)
total_count_up = 0
total_count_down = 0

# PostgreSQL Configuration
db_conn = None
cursor = None

def init_database():
    """Initializes the PostgreSQL database connection."""
    global db_conn, cursor
    try:
        db_conn = psycopg2.connect(
            dbname="person_counter",
            user="magang",
            password="magang123#",
            host="10.98.33.122",
            port="5433"
        )
        cursor = db_conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deteksi_kendaraan_directional (
                id SERIAL PRIMARY KEY,
                motor_up INTEGER NOT NULL,
                motor_down INTEGER NOT NULL,
                mobil_up INTEGER NOT NULL,
                mobil_down INTEGER NOT NULL,
                truk_up INTEGER NOT NULL,
                truk_down INTEGER NOT NULL,
                bus_up INTEGER NOT NULL,
                bus_down INTEGER NOT NULL,
                total_up INTEGER NOT NULL,
                total_down INTEGER NOT NULL,
                session_name VARCHAR(100),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        db_conn.commit()
        print("Database initialized successfully.")
    except psycopg2.Error as e:
        print(f"Database initialization error: {e}")

init_database()

# Video source
capture = None

def set_youtube_source(youtube_url):
    """Sets the video source to a YouTube video."""
    global capture
    if capture:
        capture.release()

    # Use pytube to get the YouTube stream URL
    yt = YouTube(youtube_url)
    stream = yt.streams.filter(res="360p", mime_type="video/mp4").first()
    if not stream:
        raise Exception("No suitable stream found for YouTube video.")
    stream_url = stream.url
    capture = cv2.VideoCapture(stream_url)


def process_frame():
    """Processes the video frames and performs vehicle detection."""
    global counted_ids, vehicle_count_up, vehicle_count_down, total_count_up, total_count_down
    while True:
        if not capture or not capture.isOpened():
            continue

        ret, frame = capture.read()
        if not ret:
            break

        # YOLO detection
        results = model(frame, verbose=False, conf=0.25)
        for result in results:
            for box in result.boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                if cls in vehicle_classes and conf > 0.2:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].numpy())
                    label = class_names.get(cls, 'unknown')
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Encode frame to JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        # Stream frame
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/')
def index():
    """Home page."""
    return render_template('index.html')


@app.route('/set_source', methods=['POST'])
def set_source():
    """Sets the video source."""
    try:
        data = request.json
        youtube_url = data['youtube_url']

        # Set the YouTube video source
        set_youtube_source(youtube_url)
        return jsonify({'status': 'success', 'message': 'YouTube video source set successfully.'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/video_feed')
def video_feed():
    """Video streaming route."""
    return Response(process_frame(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/save_counts', methods=['POST'])
def save_counts():
    """Save vehicle counts to the database."""
    global vehicle_count_up, vehicle_count_down, total_count_up, total_count_down
    session_name = request.json.get('session_name', f"Session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
    try:
        cursor.execute('''
            INSERT INTO deteksi_kendaraan_directional 
            (motor_up, motor_down, mobil_up, mobil_down, truk_up, truk_down, 
            bus_up, bus_down, total_up, total_down, session_name, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        ''', (
            vehicle_count_up['motorcycle'], vehicle_count_down['motorcycle'],
            vehicle_count_up['car'], vehicle_count_down['car'],
            vehicle_count_up['truck'], vehicle_count_down['truck'],
            vehicle_count_up['bus'], vehicle_count_down['bus'],
            total_count_up, total_count_down, session_name, datetime.datetime.now()
        ))
        db_conn.commit()
        return jsonify({'status': 'success', 'message': 'Counts saved successfully!'}), 200
    except psycopg2.Error as e:
        db_conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)