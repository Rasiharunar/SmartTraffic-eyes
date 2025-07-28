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
CREATE DATABASE IF NOT EXISTS vehicle_counter;
USE vehicle_counter;

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
                # FIX: Corrected database name to 'vehicle_counter'
                database='vehicle_counter'
            )
            print("✅ Koneksi database berhasil")
        except mysql.connector.Error as e:
            print(f"❌ Error koneksi database: {e}")
            messagebox.showerror("Database Error", f"Gagal koneksi ke database: {e}")
    
    def create_table(self):
        """Buat tabel jika belum ada"""
        if not self.connection: return
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vehicle_records (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    mobil INT DEFAULT 0, truck INT DEFAULT 0,
                    bus INT DEFAULT 0, motor INT DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.connection.commit()
            print("✅ Tabel vehicle_records siap")
        except mysql.connector.Error as e:
            print(f"❌ Error membuat tabel: {e}")
    
    def insert_record(self, mobil, truck, bus, motor):
        """Insert record baru ke database"""
        if not self.connection: return False
        try:
            cursor = self.connection.cursor()
            query = "INSERT INTO vehicle_records (mobil, truck, bus, motor, timestamp) VALUES (%s, %s, %s, %s, %s)"
            values = (mobil, truck, bus, motor, datetime.now())
            cursor.execute(query, values)
            self.connection.commit()
            return True
        except mysql.connector.Error as e:
            print(f"❌ Error insert record: {e}")
            return False
    
    def get_recent_records(self, limit=10):
        """Ambil record terbaru"""
        if not self.connection: return []
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT id, mobil, truck, bus, motor, timestamp FROM vehicle_records ORDER BY timestamp DESC LIMIT %s", (limit,))
            return cursor.fetchall()
        except mysql.connector.Error as e:
            print(f"❌ Error mengambil records: {e}")
            return []
    
    def get_daily_summary(self):
        """Ambil ringkasan harian"""
        default_summary = {'mobil': 0, 'truck': 0, 'bus': 0, 'motor': 0}
        if not self.connection: return default_summary
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT SUM(mobil), SUM(truck), SUM(bus), SUM(motor)
                FROM vehicle_records 
                WHERE DATE(timestamp) = CURDATE()
            """)
            result = cursor.fetchone()
            return {'mobil': result[0] or 0, 'truck': result[1] or 0, 'bus': result[2] or 0, 'motor': result[3] or 0}
        except mysql.connector.Error as e:
            print(f"❌ Error mengambil summary: {e}")
            return default_summary

    # NEW: Function to reset all data in the table
    def reset_all_records(self):
        """Hapus semua record dari tabel."""
        if not self.connection: return False
        try:
            cursor = self.connection.cursor()
            cursor.execute("TRUNCATE TABLE vehicle_records")
            self.connection.commit()
            print("🗑️ Tabel vehicle_records telah direset.")
            return True
        except mysql.connector.Error as e:
            print(f"❌ Error mereset tabel: {e}")
            return False

class ModernVehicleCounter:
    def __init__(self):
        self.CAPTURE_REGION = {"top": 100, "left": 100, "width": 800, "height": 600}
        self.MODEL_PATH = "yolo-Weights/yolov8n.pt"
        self.TARGET_CLASSES = [2, 3, 5, 7]  # car, motorcycle, bus, truck
        self.CONFIDENCE_THRESHOLD = 0.3
        self.class_mapping = {2: 'mobil', 3: 'motor', 5: 'bus', 7: 'truck'}
        
        self.model = YOLO(self.MODEL_PATH)
        self.db = DatabaseManager()
        
        self.counting_line = None
        self.setting_line = False
        self.temp_points = []
        
        self.tracked_objects = {}
        self.next_id = 0
        self.counts = {'mobil': 0, 'truck': 0, 'bus': 0, 'motor': 0}
        
        self.max_disappeared = 15
        self.max_distance = 80
        
        # NEW: Control flags for preview and main loop
        self.running = False
        self.preview_running = False
        self.current_frame = None
        
        self.setup_ui()
        
    def setup_ui(self):
        self.root = tk.Tk()
        self.root.title("🚗 Smart Vehicle Counter v2.1")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2c3e50')
        
        # Main container
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        title_label = ttk.Label(main_frame, text="🚗 SMART VEHICLE COUNTER", font=('Arial', 16, 'bold'), background='#2c3e50', foreground='white')
        title_label.pack(pady=(0, 20))
        
        top_section = tk.Frame(main_frame, bg='#2c3e50')
        top_section.pack(fill=tk.BOTH, expand=True)
        
        left_panel = tk.Frame(top_section, bg='#34495e', relief=tk.RAISED, bd=2)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        video_frame = tk.Frame(left_panel, bg='#2c3e50', relief=tk.SUNKEN, bd=2)
        video_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        self.video_label = tk.Label(video_frame, text="📹\nClick PREVIEW to see the feed", font=('Arial', 14), bg='#2c3e50', fg='white')
        self.video_label.pack(expand=True)
        
        # --- Control buttons ---
        control_frame = tk.Frame(left_panel, bg='#34495e')
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # NEW: Preview button
        self.preview_btn = tk.Button(control_frame, text="👁️ PREVIEW", command=self.start_preview, bg='#16a085', fg='white', font=('Arial', 12, 'bold'), relief=tk.FLAT, padx=10, pady=10)
        self.preview_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        self.start_btn = tk.Button(control_frame, text="▶️ START", command=self.start_counting, bg='#27ae60', fg='white', font=('Arial', 12, 'bold'), relief=tk.FLAT, padx=10, pady=10)
        self.start_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.stop_btn = tk.Button(control_frame, text="⏹️ STOP", command=self.stop_all, bg='#c0392b', fg='white', font=('Arial', 12, 'bold'), relief=tk.FLAT, padx=10, pady=10, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # --- Line control buttons ---
        line_control_frame = tk.Frame(left_panel, bg='#34495e')
        line_control_frame.pack(fill=tk.X, padx=10, pady=(0,10))

        self.line_btn = tk.Button(line_control_frame, text="📏 SET LINE", command=self.set_line_mode, bg='#2980b9', fg='white', font=('Arial', 12, 'bold'), relief=tk.FLAT, padx=10, pady=10, state=tk.DISABLED)
        self.line_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # NEW: Reset Line button
        self.reset_line_btn = tk.Button(line_control_frame, text="🔄 RESET LINE", command=self.reset_line, bg='#f39c12', fg='white', font=('Arial', 12, 'bold'), relief=tk.FLAT, padx=10, pady=10, state=tk.DISABLED)
        self.reset_line_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # --- Right Panel ---
        right_panel = tk.Frame(top_section, bg='#34495e', relief=tk.RAISED, bd=2, width=400)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0), pady=0)
        right_panel.pack_propagate(False)

        counter_frame = tk.LabelFrame(right_panel, text="📊 LIVE COUNTERS", bg='#34495e', fg='white', font=('Arial', 12, 'bold'))
        counter_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.counter_vars = {}
        counter_colors = {'mobil': '#3498db', 'truck': '#e67e22', 'bus': '#2ecc71', 'motor': '#d35400'}
        for vehicle_type in ['mobil', 'truck', 'bus', 'motor']:
            frame = tk.Frame(counter_frame, bg=counter_colors[vehicle_type], relief=tk.RAISED, bd=2)
            frame.pack(fill=tk.X, padx=5, pady=5)
            icon = "🚗" if vehicle_type == 'mobil' else "🚛" if vehicle_type == 'truck' else "🚌" if vehicle_type == 'bus' else "🏍️"
            tk.Label(frame, text=f"{icon} {vehicle_type.upper()}", bg=counter_colors[vehicle_type], fg='white', font=('Arial', 12, 'bold')).pack(side=tk.LEFT, padx=10, pady=5)
            self.counter_vars[vehicle_type] = tk.StringVar(value="0")
            tk.Label(frame, textvariable=self.counter_vars[vehicle_type], bg=counter_colors[vehicle_type], fg='white', font=('Arial', 20, 'bold')).pack(side=tk.RIGHT, padx=10, pady=5)
        
        summary_frame = tk.LabelFrame(right_panel, text="📈 TODAY'S SUMMARY", bg='#34495e', fg='white', font=('Arial', 12, 'bold'))
        summary_frame.pack(fill=tk.X, padx=10, pady=10)
        self.summary_text = tk.Text(summary_frame, height=6, bg='#2c3e50', fg='white', font=('Courier', 10), relief=tk.FLAT, wrap=tk.WORD)
        self.summary_text.pack(fill=tk.X, padx=5, pady=5)
        
        records_frame = tk.LabelFrame(right_panel, text="📋 RECENT RECORDS", bg='#34495e', fg='white', font=('Arial', 12, 'bold'))
        records_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        columns = ('ID', 'Mobil', 'Truck', 'Bus', 'Motor', 'Time')
        self.records_tree = ttk.Treeview(records_frame, columns=columns, show='headings', height=5)
        for col in columns:
            self.records_tree.heading(col, text=col)
            self.records_tree.column(col, width=60, anchor=tk.CENTER)
        self.records_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5,0), pady=5)
        
        # --- Data Management Buttons ---
        data_mgmt_frame = tk.LabelFrame(right_panel, text="🗃️ DATA MANAGEMENT", bg='#34495e', fg='white', font=('Arial', 12, 'bold'))
        data_mgmt_frame.pack(fill=tk.X, padx=10, pady=10)

        self.save_btn = tk.Button(data_mgmt_frame, text="💾 SAVE COUNTS", command=self.save_to_database, bg='#8e44ad', fg='white', font=('Arial', 12, 'bold'), relief=tk.FLAT, padx=10, pady=10)
        self.save_btn.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)

        # NEW: Reset DB button
        self.reset_db_btn = tk.Button(data_mgmt_frame, text="🗑️ RESET DB", command=self.reset_database_data, bg='#e74c3c', fg='white', font=('Arial', 12, 'bold'), relief=tk.FLAT, padx=10, pady=10)
        self.reset_db_btn.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        self.status_var = tk.StringVar(value="🔴 Ready")
        status_bar = tk.Label(main_frame, textvariable=self.status_var, bg='#1abc9c', fg='white', font=('Arial', 10, 'bold'), relief=tk.SUNKEN, bd=1, anchor='w', padx=10)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.update_summary()
        self.update_records()
        self.root.after(30000, self.auto_refresh)
    
    # --- New and Modified Control Functions ---
    def start_preview(self):
        self.stop_all(silent=True)
        self.preview_running = True
        self.toggle_buttons_state(is_running=True)
        self.status_var.set("👁️ PREVIEW - Set your counting line now")
        threading.Thread(target=self.preview_loop, daemon=True).start()

    def start_counting(self):
        if self.counting_line is None:
            messagebox.showwarning("Warning", "Please set a counting line first using the PREVIEW mode.")
            return
        self.stop_all(silent=True)
        self.running = True
        self.toggle_buttons_state(is_running=True)
        self.status_var.set("🟢 COUNTING - Vehicle detection is active")
        threading.Thread(target=self.video_loop, daemon=True).start()

    def stop_all(self, silent=False):
        self.running = False
        self.preview_running = False
        self.toggle_buttons_state(is_running=False)
        if not silent:
            self.status_var.set("🔴 STOPPED - Ready to start")
            # You might want to clear the video label when stopped
            # self.video_label.config(image='', text="📹\nClick PREVIEW to see the feed")
    
    def toggle_buttons_state(self, is_running):
        state_if_running = tk.DISABLED
        state_if_stopped = tk.NORMAL
        
        self.preview_btn.config(state=state_if_running if is_running else state_if_stopped)
        self.start_btn.config(state=state_if_running if is_running else state_if_stopped)
        self.stop_btn.config(state=state_if_stopped if is_running else state_if_running)
        self.line_btn.config(state=state_if_stopped if is_running else state_if_running)
        self.reset_line_btn.config(state=state_if_stopped if is_running else state_if_running)

    def set_line_mode(self):
        self.setting_line = True
        self.temp_points = []
        self.status_var.set("📏 Click 2 points on video to set counting line")

    def reset_line(self):
        self.counting_line = None
        self.setting_line = False
        self.temp_points = []
        self.status_var.set("👍 Line has been reset. You can set a new one.")

    def reset_database_data(self):
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to delete ALL records from the database? This action cannot be undone."):
            if self.db.reset_all_records():
                # Reset live counters as well
                for v_type in self.counts:
                    self.counts[v_type] = 0
                    self.counter_vars[v_type].set("0")
                self.update_summary()
                self.update_records()
                messagebox.showinfo("Success", "Database has been reset successfully.")
            else:
                messagebox.showerror("Error", "Failed to reset database.")

    def auto_refresh(self):
        if not self.running and not self.preview_running:
            self.update_summary()
            self.update_records()
        self.root.after(30000, self.auto_refresh)
    
    # --- Loops and Core Logic (mostly unchanged, with new preview loop) ---
    def preview_loop(self):
        """Lightweight loop for previewing feed and setting line."""
        sct = mss.mss()
        while self.preview_running:
            try:
                frame = np.array(sct.grab(self.CAPTURE_REGION))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                self.draw_interface(frame) # Draw line, but no boxes
                self.update_video_label(frame)
            except Exception as e:
                print(f"Error in preview loop: {e}")
            time.sleep(0.033) # ~30 FPS

    def video_loop(self):
        """Main video loop with YOLO detection."""
        sct = mss.mss()
        prev_time = time.time()
        while self.running:
            try:
                frame = np.array(sct.grab(self.CAPTURE_REGION))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                
                results = self.model.predict(frame, conf=self.CONFIDENCE_THRESHOLD, classes=self.TARGET_CLASSES, verbose=False)
                
                detections = []
                if results[0].boxes:
                    for box in results[0].boxes:
                        x1, y1, x2, y2 = box.xyxy[0]
                        detections.append(([x1, y1, x2, y2], box.conf[0], int(box.cls[0])))
                
                self.update_tracking(detections)
                self.draw_interface(frame)
                
                current_time = time.time()
                fps = 1 / (current_time - prev_time)
                prev_time = current_time
                cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                self.update_video_label(frame)
            except Exception as e:
                print(f"Error in video loop: {e}")
            time.sleep(0.01) # Faster polling for detection

    def update_video_label(self, frame):
        """Converts a CV2 frame and updates the Tkinter label."""
        self.current_frame = frame
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_pil = Image.fromarray(frame_rgb)
        frame_tk = ImageTk.PhotoImage(image=frame_pil)
        
        self.video_label.configure(image=frame_tk, text="")
        self.video_label.image = frame_tk
        self.video_label.bind("<Button-1>", self.on_video_click)

    # --- Other helper functions (unchanged) ---
    def save_to_database(self):
        if sum(self.counts.values()) == 0:
            messagebox.showwarning("Warning", "No new vehicles counted to save!")
            return
        if self.db.insert_record(self.counts['mobil'], self.counts['truck'], self.counts['bus'], self.counts['motor']):
            messagebox.showinfo("Success", "Data saved to database!")
            for v_type in self.counts:
                self.counts[v_type] = 0
                self.counter_vars[v_type].set("0")
            self.update_summary()
            self.update_records()
        else:
            messagebox.showerror("Error", "Failed to save data to database!")
    
    def on_video_click(self, event):
        if self.setting_line and self.current_frame is not None:
            x = int(event.x * (self.current_frame.shape[1] / self.video_label.winfo_width()))
            y = int(event.y * (self.current_frame.shape[0] / self.video_label.winfo_height()))
            self.temp_points.append((x, y))
            if len(self.temp_points) == 2:
                self.counting_line = self.temp_points.copy()
                self.setting_line = False
                self.temp_points = []
                self.status_var.set(f"✅ Line set. Press START to begin counting.")

    def update_summary(self):
        summary = self.db.get_daily_summary()
        total = sum(summary.values())
        text = (f"📊 TODAY'S TRAFFIC SUMMARY\n{'='*30}\n"
                f"🚗 Cars:     {summary.get('mobil', 0):>8}\n"
                f"🚛 Trucks:   {summary.get('truck', 0):>8}\n"
                f"🚌 Buses:    {summary.get('bus', 0):>8}\n"
                f"🏍️ Motors:   {summary.get('motor', 0):>8}\n"
                f"{'='*30}\n📈 Total:    {total:>8}")
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(1.0, text)
        self.summary_text.config(state=tk.DISABLED)

    def update_records(self):
        for item in self.records_tree.get_children(): self.records_tree.delete(item)
        for record in self.db.get_recent_records(10):
            time_str = record[5].strftime("%H:%M:%S")
            self.records_tree.insert('', 0, values=(record[0], record[1], record[2], record[3], record[4], time_str))

    def calculate_distance(self, p1, p2): return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    def get_center_point(self, box): return (int((box[0] + box[2]) / 2), int((box[1] + box[3]) / 2))
    def line_intersection(self, p1, p2, p3, p4):
        x1, y1 = p1; x2, y2 = p2; x3, y3 = p3; x4, y4 = p4
        denom = (x1-x2)*(y3-y4) - (y1-y2)*(x3-x4)
        if denom == 0: return False
        t = ((x1-x3)*(y3-y4) - (y1-y3)*(x3-x4)) / denom
        u = -((x1-x2)*(y1-y3) - (y1-y2)*(x1-x3)) / denom
        return 0 <= t <= 1 and 0 <= u <= 1

    def check_line_crossing(self, prev_center, curr_center, vehicle_class):
        if self.counting_line and self.line_intersection(prev_center, curr_center, self.counting_line[0], self.counting_line[1]):
            v_type = self.class_mapping.get(vehicle_class)
            if v_type:
                self.counts[v_type] += 1
                self.counter_vars[v_type].set(str(self.counts[v_type]))
                return True
        return False

    def update_tracking(self, detections):
        current_centers = [self.get_center_point(d[0]) for d in detections]
        used_detection_indices = set()
        for obj_id in list(self.tracked_objects.keys()):
            self.tracked_objects[obj_id]["disappeared"] += 1
            min_dist, best_match_idx = float('inf'), -1
            for i, center in enumerate(current_centers):
                if i in used_detection_indices: continue
                dist = self.calculate_distance(self.tracked_objects[obj_id]["center"], center)
                if dist < self.max_distance and dist < min_dist: min_dist, best_match_idx = dist, i
            if best_match_idx != -1:
                old_center = self.tracked_objects[obj_id]["center"]
                if not self.tracked_objects[obj_id]["counted"]:
                    if self.check_line_crossing(old_center, current_centers[best_match_idx], detections[best_match_idx][2]):
                        self.tracked_objects[obj_id]["counted"] = True
                
                self.tracked_objects[obj_id].update({
                    "center": current_centers[best_match_idx], "box": detections[best_match_idx][0],
                    "class": detections[best_match_idx][2], "confidence": detections[best_match_idx][1], "disappeared": 0
                })
                used_detection_indices.add(best_match_idx)
        for obj_id in list(self.tracked_objects.keys()):
            if self.tracked_objects[obj_id]["disappeared"] > self.max_disappeared:
                del self.tracked_objects[obj_id]
        for i, (box, conf, cls_id) in enumerate(detections):
            if i not in used_detection_indices:
                self.tracked_objects[self.next_id] = {"center": self.get_center_point(box), "box": box, "class": cls_id, "confidence": conf, "disappeared": 0, "counted": False}
                self.next_id += 1

    def draw_interface(self, frame):
        if self.counting_line:
            cv2.line(frame, self.counting_line[0], self.counting_line[1], (0, 0, 255), 3)
            cv2.putText(frame, "COUNTING LINE", (self.counting_line[0][0], self.counting_line[0][1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        if self.setting_line and len(self.temp_points) == 1:
            cv2.circle(frame, self.temp_points[0], 5, (255, 0, 0), -1)
        
        # Draw tracked objects only if main loop is running
        if self.running:
            colors = {2: (255, 0, 0), 3: (0, 255, 0), 5: (0, 0, 255), 7: (255, 255, 0)}
            for obj_id, data in self.tracked_objects.items():
                box, center, cls_id, conf, counted = data["box"], data["center"], data["class"], data["confidence"], data["counted"]
                x1, y1, x2, y2 = map(int, box)
                color = (0, 255, 255) if counted else colors.get(cls_id, (255, 255, 255))
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.circle(frame, center, 4, color, -1)
                label = f"ID:{obj_id} {self.class_mapping.get(cls_id, 'N/A')}"
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    print("🚗 Starting Smart Vehicle Counter...")
    print("⚠️  Make sure MySQL is running and the 'vehicle_counter' database exists.")
    app = ModernVehicleCounter()
    app.run()