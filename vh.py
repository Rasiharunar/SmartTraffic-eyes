import cv2
import numpy as np
import mss
import time
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from ultralytics import YOLO
import mysql.connector
from datetime import datetime
from PIL import Image, ImageTk

# SQL to create the database (run this in your MySQL client if needed)
CREATE_DATABASE_SQL = """
CREATE DATABASE IF NOT EXISTS vehicle_counting;
USE vehicle_counting;

CREATE TABLE IF NOT EXISTS vehicle_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mobil INT DEFAULT 0,
    truck INT DEFAULT 0,
    bus INT DEFAULT 0,
    motor INT DEFAULT 0,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.connect_to_database()
        if self.connection:
            self.create_table()
    
    def connect_to_database(self):
        """Koneksi ke database MySQL"""
        try:
            self.connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password='',
                # FIX: Corrected database name
                database='vehicle_counter'
            )
            print("✅ Koneksi database berhasil")
        except mysql.connector.Error as e:
            print(f"❌ Error koneksi database: {e}")
            messagebox.showerror("Database Error", f"Gagal koneksi ke database: {e}")
    
    def create_table(self):
        """Buat tabel jika belum ada"""
        if not self.connection:
            return
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vehicle_records (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    mobil INT DEFAULT 0,
                    truck INT DEFAULT 0,
                    bus INT DEFAULT 0,
                    motor INT DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.connection.commit()
            print("✅ Tabel vehicle_records siap")
        except mysql.connector.Error as e:
            print(f"❌ Error membuat tabel: {e}")
    
    def insert_record(self, mobil, truck, bus, motor):
        """Insert record baru ke database"""
        if not self.connection:
            return False
        try:
            cursor = self.connection.cursor()
            query = """
                INSERT INTO vehicle_records (mobil, truck, bus, motor, timestamp)
                VALUES (%s, %s, %s, %s, %s)
            """
            values = (mobil, truck, bus, motor, datetime.now())
            cursor.execute(query, values)
            self.connection.commit()
            return True
        except mysql.connector.Error as e:
            print(f"❌ Error insert record: {e}")
            return False
    
    def get_recent_records(self, limit=10):
        """Ambil record terbaru"""
        if not self.connection:
            return []
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT id, mobil, truck, bus, motor, timestamp 
                FROM vehicle_records 
                ORDER BY timestamp DESC 
                LIMIT %s
            """, (limit,))
            return cursor.fetchall()
        except mysql.connector.Error as e:
            print(f"❌ Error mengambil records: {e}")
            return []
    
    def get_daily_summary(self):
        """Ambil ringkasan harian"""
        # FIX: Return a default dictionary on failure to prevent KeyError
        default_summary = {'mobil': 0, 'truck': 0, 'bus': 0, 'motor': 0}
        if not self.connection:
            return default_summary
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT 
                    SUM(mobil) as total_mobil,
                    SUM(truck) as total_truck, 
                    SUM(bus) as total_bus,
                    SUM(motor) as total_motor
                FROM vehicle_records 
                WHERE DATE(timestamp) = CURDATE()
            """)
            result = cursor.fetchone()
            return {
                'mobil': result[0] or 0,
                'truck': result[1] or 0,
                'bus': result[2] or 0,
                'motor': result[3] or 0
            }
        except mysql.connector.Error as e:
            print(f"❌ Error mengambil summary: {e}")
            return default_summary

class ModernVehicleCounter:
    def __init__(self):
        # Konfigurasi dasar
        self.CAPTURE_REGION = {"top": 100, "left": 100, "width": 800, "height": 600}
        self.MODEL_PATH = "yolo-Weights/yolov8n.pt"
        self.TARGET_CLASSES = [2, 3, 5, 7]  # car, motorcycle, bus, truck
        self.CONFIDENCE_THRESHOLD = 0.3
        
        # Class mapping untuk database
        self.class_mapping = {
            2: 'mobil',    # car
            3: 'motor',    # motorcycle  
            5: 'bus',      # bus
            7: 'truck'     # truck
        }
        
        # Load YOLO
        self.model = YOLO(self.MODEL_PATH)
        self.COCO_LABELS = self.model.names
        # FIX: Do not initialize mss here; it's not thread-safe
        
        # Database manager
        self.db = DatabaseManager()
        
        # Variabel untuk garis pembatas
        self.counting_line = None
        self.setting_line = False
        self.temp_points = []
        
        # Variabel untuk tracking dan counting
        self.tracked_objects = {}
        self.next_id = 0
        
        # Counters untuk setiap jenis kendaraan
        self.counts = {
            'mobil': 0,
            'truck': 0,
            'bus': 0,
            'motor': 0
        }
        
        # Parameter tracking
        self.max_disappeared = 15
        self.max_distance = 80
        
        # Control variables
        self.running = False
        self.current_frame = None
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        """Setup antarmuka pengguna modern"""
        self.root = tk.Tk()
        self.root.title("🚗 Smart Vehicle Counter v2.0")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2c3e50')
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), background='#2c3e50', foreground='white')
        style.configure('Counter.TLabel', font=('Arial', 24, 'bold'), background='#34495e', foreground='#ecf0f1')
        style.configure('Info.TLabel', font=('Arial', 10), background='#2c3e50', foreground='#bdc3c7')
        
        # Main container
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="🚗 SMART VEHICLE COUNTER", style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Top section - Controls and Video
        top_section = tk.Frame(main_frame, bg='#2c3e50')
        top_section.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Video and controls
        left_panel = tk.Frame(top_section, bg='#34495e', relief=tk.RAISED, bd=2)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Video frame
        video_frame = tk.Frame(left_panel, bg='#2c3e50', relief=tk.SUNKEN, bd=2)
        video_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        self.video_label = tk.Label(video_frame, text="📹 LIVE FEED\nPress START to begin", 
                                   font=('Arial', 14), bg='#2c3e50', fg='white')
        self.video_label.pack(expand=True)
        
        # Control buttons
        control_frame = tk.Frame(left_panel, bg='#34495e')
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.start_btn = tk.Button(control_frame, text="▶️ START", command=self.start_counting,
                                  bg='#27ae60', fg='white', font=('Arial', 12, 'bold'),
                                  relief=tk.FLAT, padx=20, pady=10)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(control_frame, text="⏹️ STOP", command=self.stop_counting,
                                 bg='#e74c3c', fg='white', font=('Arial', 12, 'bold'),
                                 relief=tk.FLAT, padx=20, pady=10, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.line_btn = tk.Button(control_frame, text="📏 SET LINE", command=self.set_line_mode,
                                 bg='#3498db', fg='white', font=('Arial', 12, 'bold'),
                                 relief=tk.FLAT, padx=20, pady=10)
        self.line_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = tk.Button(control_frame, text="💾 SAVE TO DB", command=self.save_to_database,
                                 bg='#9b59b6', fg='white', font=('Arial', 12, 'bold'),
                                 relief=tk.FLAT, padx=20, pady=10)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        # Right panel - Statistics and data
        right_panel = tk.Frame(top_section, bg='#34495e', relief=tk.RAISED, bd=2, width=400)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0), pady=0)
        right_panel.pack_propagate(False)

        # Live counters
        counter_frame = tk.LabelFrame(right_panel, text="📊 LIVE COUNTERS", 
                                     bg='#34495e', fg='white', font=('Arial', 12, 'bold'))
        counter_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.counter_vars = {}
        counter_colors = {'mobil': '#3498db', 'truck': '#e67e22', 'bus': '#2ecc71', 'motor': '#f39c12'}
        
        for vehicle_type in ['mobil', 'truck', 'bus', 'motor']:
            frame = tk.Frame(counter_frame, bg=counter_colors[vehicle_type], relief=tk.RAISED, bd=2)
            frame.pack(fill=tk.X, padx=5, pady=5)
            
            icon = "🚗" if vehicle_type == 'mobil' else "🚛" if vehicle_type == 'truck' else "🚌" if vehicle_type == 'bus' else "🏍️"
            
            tk.Label(frame, text=f"{icon} {vehicle_type.upper()}", 
                    bg=counter_colors[vehicle_type], fg='white', 
                    font=('Arial', 12, 'bold')).pack(side=tk.LEFT, padx=10, pady=5)
            
            self.counter_vars[vehicle_type] = tk.StringVar(value="0")
            tk.Label(frame, textvariable=self.counter_vars[vehicle_type],
                    bg=counter_colors[vehicle_type], fg='white',
                    font=('Arial', 20, 'bold')).pack(side=tk.RIGHT, padx=10, pady=5)
        
        # Daily summary
        summary_frame = tk.LabelFrame(right_panel, text="📈 TODAY'S SUMMARY", 
                                     bg='#34495e', fg='white', font=('Arial', 12, 'bold'))
        summary_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.summary_text = tk.Text(summary_frame, height=6, bg='#2c3e50', fg='white',
                                   font=('Courier', 10), relief=tk.FLAT, wrap=tk.WORD)
        self.summary_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Recent records
        records_frame = tk.LabelFrame(right_panel, text="📋 RECENT RECORDS", 
                                     bg='#34495e', fg='white', font=('Arial', 12, 'bold'))
        records_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ('ID', 'Mobil', 'Truck', 'Bus', 'Motor', 'Time')
        self.records_tree = ttk.Treeview(records_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.records_tree.heading(col, text=col)
            self.records_tree.column(col, width=60, anchor=tk.CENTER)
        
        scrollbar = ttk.Scrollbar(records_frame, orient=tk.VERTICAL, command=self.records_tree.yview)
        self.records_tree.configure(yscrollcommand=scrollbar.set)
        
        self.records_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5,0), pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="🔴 Ready - Press START to begin counting")
        status_bar = tk.Label(main_frame, textvariable=self.status_var, 
                             bg='#1abc9c', fg='white', font=('Arial', 10, 'bold'),
                             relief=tk.SUNKEN, bd=1, anchor='w', padx=10)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Load initial data
        self.update_summary()
        self.update_records()
        
        # Auto refresh every 30 seconds
        self.root.after(30000, self.auto_refresh)
    
    def auto_refresh(self):
        """Auto refresh data every 30 seconds"""
        if not self.running: # Only refresh if not actively counting
            self.update_summary()
            self.update_records()
        self.root.after(30000, self.auto_refresh)
    
    def update_summary(self):
        """Update daily summary"""
        summary = self.db.get_daily_summary()
        total = sum(summary.values())
        text = (
            f"📊 TODAY'S TRAFFIC SUMMARY\n"
            f"{'='*30}\n"
            f"🚗 Cars:     {summary.get('mobil', 0):>8}\n"
            f"🚛 Trucks:   {summary.get('truck', 0):>8}\n"  
            f"🚌 Buses:    {summary.get('bus', 0):>8}\n"
            f"🏍️ Motors:   {summary.get('motor', 0):>8}\n"
            f"{'='*30}\n"
            f"📈 Total:    {total:>8}"
        )
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(1.0, text)
        self.summary_text.config(state=tk.DISABLED)

    def update_records(self):
        """Update recent records table"""
        for item in self.records_tree.get_children():
            self.records_tree.delete(item)
        records = self.db.get_recent_records(10)
        for record in records:
            time_str = record[5].strftime("%H:%M:%S")
            self.records_tree.insert('', 0, values=(
                record[0], record[1], record[2], record[3], record[4], time_str
            ))
    
    def start_counting(self):
        """Start counting"""
        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("🟢 COUNTING - Click on video to set counting line")
        
        self.video_thread = threading.Thread(target=self.video_loop, daemon=True)
        self.video_thread.start()
    
    def stop_counting(self):
        """Stop counting"""
        self.running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("🔴 STOPPED - Press START to resume")
    
    def set_line_mode(self):
        """Set line mode"""
        self.setting_line = True
        self.temp_points = []
        self.status_var.set("📏 Click 2 points on video to set counting line")
    
    def save_to_database(self):
        """Save data to database"""
        if sum(self.counts.values()) == 0:
            messagebox.showwarning("Warning", "No new vehicles counted to save!")
            return
        
        success = self.db.insert_record(
            self.counts['mobil'],
            self.counts['truck'], 
            self.counts['bus'],
            self.counts['motor']
        )
        
        if success:
            messagebox.showinfo("Success", "Data saved to database!")
            # Reset counters
            for vehicle_type in self.counts:
                self.counts[vehicle_type] = 0
                self.counter_vars[vehicle_type].set("0")
            
            # Update displays
            self.update_summary()
            self.update_records()
        else:
            messagebox.showerror("Error", "Failed to save data to database!")
    
    def on_video_click(self, event):
        """Handle click on video to set line"""
        if self.setting_line and self.current_frame is not None:
            # Convert click coordinates to frame coordinates
            x = int(event.x * (self.current_frame.shape[1] / self.video_label.winfo_width()))
            y = int(event.y * (self.current_frame.shape[0] / self.video_label.winfo_height()))
            
            self.temp_points.append((x, y))
            
            if len(self.temp_points) == 2:
                self.counting_line = self.temp_points.copy()
                self.setting_line = False
                self.temp_points = []
                self.status_var.set(f"✅ Counting line set: {self.counting_line}")
    
    def video_loop(self):
        """Main video loop"""
        # FIX: Initialize mss inside the thread for thread safety
        sct = mss.mss()
        prev_time = time.time()
        
        while self.running:
            try:
                # Capture screenshot
                screenshot = sct.grab(self.CAPTURE_REGION)
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                
                # YOLO detection
                results = self.model.predict(frame, 
                                           conf=self.CONFIDENCE_THRESHOLD,
                                           classes=self.TARGET_CLASSES,
                                           verbose=False)
                
                detections = []
                if len(results[0].boxes) > 0:
                    for box in results[0].boxes:
                        x1, y1, x2, y2 = box.xyxy[0]
                        conf = box.conf[0]
                        cls_id = int(box.cls[0])
                        detections.append(([x1, y1, x2, y2], conf, cls_id))
                
                self.update_tracking(detections)
                self.draw_interface(frame)
                
                current_time = time.time()
                fps = 1 / (current_time - prev_time)
                prev_time = current_time
                cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                self.current_frame = frame
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_pil = Image.fromarray(frame_rgb)
                frame_tk = ImageTk.PhotoImage(image=frame_pil)
                
                self.video_label.configure(image=frame_tk, text="")
                self.video_label.image = frame_tk
                self.video_label.bind("<Button-1>", self.on_video_click)
                
            except Exception as e:
                print(f"Error in video loop: {e}")
                time.sleep(0.1)
    
    def calculate_distance(self, point1, point2):
        return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    
    def get_center_point(self, box):
        x1, y1, x2, y2 = box
        return (int((x1 + x2) / 2), int((y1 + y2) / 2))
    
    def line_intersection(self, p1, p2, p3, p4):
        x1, y1 = p1; x2, y2 = p2
        x3, y3 = p3; x4, y4 = p4
        denom = (x1-x2)*(y3-y4) - (y1-y2)*(x3-x4)
        if denom == 0: return False
        t = ((x1-x3)*(y3-y4) - (y1-y3)*(x3-x4)) / denom
        u = -((x1-x2)*(y1-y3) - (y1-y2)*(x1-x3)) / denom
        return 0 <= t <= 1 and 0 <= u <= 1
    
    def check_line_crossing(self, prev_center, curr_center, vehicle_class):
        if self.counting_line and self.line_intersection(prev_center, curr_center, self.counting_line[0], self.counting_line[1]):
            vehicle_type = self.class_mapping.get(vehicle_class)
            if vehicle_type:
                self.counts[vehicle_type] += 1
                self.counter_vars[vehicle_type].set(str(self.counts[vehicle_type]))
                print(f"✅ {vehicle_type.upper()} crossed! Total: {self.counts[vehicle_type]}")
                return True
        return False
    
    def update_tracking(self, detections):
        """Update object tracking"""
        current_centers = [self.get_center_point(d[0]) for d in detections]
        used_detection_indices = set()
        
        for obj_id in list(self.tracked_objects.keys()):
            self.tracked_objects[obj_id]["disappeared"] += 1
            min_distance = float('inf')
            best_match_idx = -1
            
            for i, center in enumerate(current_centers):
                if i in used_detection_indices: continue
                distance = self.calculate_distance(self.tracked_objects[obj_id]["center"], center)
                if distance < self.max_distance and distance < min_distance:
                    min_distance = distance
                    best_match_idx = i
            
            if best_match_idx != -1:
                old_center = self.tracked_objects[obj_id]["center"]
                new_center = current_centers[best_match_idx]
                
                if not self.tracked_objects[obj_id]["counted"]:
                    if self.check_line_crossing(old_center, new_center, detections[best_match_idx][2]):
                        self.tracked_objects[obj_id]["counted"] = True
                
                self.tracked_objects[obj_id]["center"] = new_center
                self.tracked_objects[obj_id]["box"] = detections[best_match_idx][0]
                self.tracked_objects[obj_id]["class"] = detections[best_match_idx][2]
                self.tracked_objects[obj_id]["confidence"] = detections[best_match_idx][1]
                self.tracked_objects[obj_id]["disappeared"] = 0
                used_detection_indices.add(best_match_idx)
        
        for obj_id in list(self.tracked_objects.keys()):
            if self.tracked_objects[obj_id]["disappeared"] > self.max_disappeared:
                del self.tracked_objects[obj_id]
        
        for i in range(len(detections)):
            if i not in used_detection_indices:
                box, conf, cls_id = detections[i]
                center = self.get_center_point(box)
                self.tracked_objects[self.next_id] = {
                    "center": center, "box": box, "class": cls_id,
                    "confidence": conf, "disappeared": 0, "counted": False
                }
                self.next_id += 1
    
    def draw_interface(self, frame):
        """Draw interface on the frame"""
        if self.counting_line:
            cv2.line(frame, self.counting_line[0], self.counting_line[1], (0, 0, 255), 3)
            cv2.putText(frame, "COUNTING LINE", (self.counting_line[0][0], self.counting_line[0][1] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        if self.setting_line and len(self.temp_points) == 1:
            cv2.circle(frame, self.temp_points[0], 5, (255, 0, 0), -1)
        
        colors = {2: (255, 0, 0), 3: (0, 255, 0), 5: (0, 0, 255), 7: (255, 255, 0)}
        
        for obj_id, data in self.tracked_objects.items():
            box = data["box"]; center = data["center"]; cls_id = data["class"]
            conf = data.get("confidence", 0); counted = data["counted"]
            x1, y1, x2, y2 = map(int, box)
            
            color = (0, 255, 255) if counted else colors.get(cls_id, (255, 255, 255))
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.circle(frame, center, 4, color, -1)
            
            label = f"ID:{obj_id} {self.class_mapping.get(cls_id, 'N/A')} {conf:.2f}"
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    def run(self):
        """Run the application"""
        self.root.mainloop()

if __name__ == "__main__":
    print("🚗 Starting Smart Vehicle Counter...")
    print("⚠️  Make sure MySQL is running and the 'vehicle_counting' database exists.")
    print("📋 You can create the database by running the SQL commands in the code.")
    
    app = ModernVehicleCounter()
    app.run()