import cv2
import numpy as np
from PIL import ImageGrab
from ultralytics import YOLO
import tkinter as tk
from tkinter import messagebox, Label, Button, Canvas, Frame
from tkinter import ttk  # Untuk combobox/dropdown
from PIL import Image, ImageTk
import time

# --- PENGATURAN SIMPLE ---
CAPTURE_REGION = {"left": 100, "top": 100, "width": 640, "height": 480}
VEHICLE_CLASSES = ['motorcycle', 'truck', 'car', 'bus']
CONFIDENCE_THRESHOLD = 0.05
MODEL_PATH = 'yolo-Weights/yolo11n.pt'

class SimpleVehicleCounter:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Vehicle Counter with Filter")
        self.root.geometry("900x650")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Load YOLO model
        print("Loading YOLO model...")
        self.model = YOLO(MODEL_PATH)
        print("Model loaded successfully!")

        # Variables
        self.is_running = False
        self.is_setting_line = False
        self.line_points = []
        self.vehicle_counts = {'car': 0, 'truck': 0, 'motorcycle': 0}
        self.counted_ids = set()
        self.last_fps_time = time.time()
        self.fps_counter = 0
        self.current_fps = 0
        
        # Filter variables
        self.selected_vehicle_filter = tk.StringVar(value="All Vehicles")

        # Setup GUI
        self._setup_gui()
        
        # Start main loop
        self.update_loop()

    def _setup_gui(self):
        main_frame = Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Video canvas
        self.canvas = Canvas(main_frame, 
                           width=CAPTURE_REGION["width"], 
                           height=CAPTURE_REGION["height"], 
                           bg="black")
        self.canvas.pack(side=tk.LEFT, padx=(0, 10))
        self.canvas.bind("<Button-1>", self.on_mouse_click)

        # Control panel
        control_frame = Frame(main_frame, width=250)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y)
        control_frame.pack_propagate(False)

        # Vehicle Filter Section
        filter_frame = Frame(control_frame)
        filter_frame.pack(pady=10, fill=tk.X)
        
        Label(filter_frame, text="🎯 VEHICLE FILTER", 
              font=("Arial", 12, "bold")).pack(pady=(0, 5))
        
        # Dropdown untuk filter kendaraan
        filter_options = ["All Vehicles", "Cars Only", "Trucks Only", "Motorcycles Only"]
        self.filter_dropdown = ttk.Combobox(filter_frame, 
                                          textvariable=self.selected_vehicle_filter,
                                          values=filter_options,
                                          state="readonly",
                                          width=18,
                                          font=("Arial", 10))
        self.filter_dropdown.pack(pady=5)
        self.filter_dropdown.bind("<<ComboboxSelected>>", self.on_filter_change)

        # Status untuk filter aktif
        self.filter_status = Label(filter_frame, text="📊 Counting: All vehicles", 
                                 font=("Arial", 9), fg="blue")
        self.filter_status.pack(pady=(5, 0))

        # Separator
        separator1 = Frame(control_frame, height=2, bg="lightgray")
        separator1.pack(fill=tk.X, pady=10)

        # Buttons
        btn_frame = Frame(control_frame)
        btn_frame.pack(pady=10, fill=tk.X)

        self.start_btn = Button(btn_frame, text="▶ START", 
                               command=self.toggle_counting, 
                               font=("Arial", 12, "bold"), 
                               bg="lightgreen", fg="darkgreen")
        self.start_btn.pack(fill=tk.X, pady=2)

        Button(btn_frame, text="📏 Set Line", 
               command=self.set_line_mode, 
               font=("Arial", 11), 
               bg="lightblue").pack(fill=tk.X, pady=2)

        Button(btn_frame, text="🔄 Reset", 
               command=self.reset_counts, 
               font=("Arial", 11), 
               bg="orange").pack(fill=tk.X, pady=2)

        # Status info
        info_frame = Frame(control_frame)
        info_frame.pack(pady=20, fill=tk.X)

        self.status_label = Label(info_frame, text="● STOPPED", 
                                font=("Arial", 12, "bold"), fg="red")
        self.status_label.pack()

        self.fps_label = Label(info_frame, text="FPS: 0", 
                             font=("Arial", 10), fg="blue")
        self.fps_label.pack(pady=5)

        # Separator
        separator2 = Frame(control_frame, height=2, bg="lightgray")
        separator2.pack(fill=tk.X, pady=10)

        # Vehicle counts
        count_frame = Frame(control_frame)
        count_frame.pack(pady=20, fill=tk.X)

        Label(count_frame, text="🚗 VEHICLE COUNT", 
              font=("Arial", 14, "bold")).pack(pady=(0, 10))

        self.count_labels = {}
        vehicles = [('car', '🚗'), ('truck', '🚛'), ('motorcycle', '🏍️')]
        
        for vehicle, emoji in vehicles:
            frame = Frame(count_frame)
            frame.pack(fill=tk.X, pady=3)
            
            label_text = Label(frame, text=f"{emoji} {vehicle.title()}:", 
                              font=("Arial", 11))
            label_text.pack(side=tk.LEFT)
            
            count_label = Label(frame, text="0", 
                              font=("Arial", 11, "bold"), 
                              fg="green", width=5)
            count_label.pack(side=tk.RIGHT)
            
            # Store both labels for easier updating
            self.count_labels[vehicle] = {
                'count': count_label,
                'text': label_text,
                'frame': frame
            }

        # Total
        total_frame = Frame(count_frame)
        total_frame.pack(fill=tk.X, pady=(15, 5))
        
        Label(total_frame, text="🔢 TOTAL:", 
              font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        
        self.total_label = Label(total_frame, text="0", 
                               font=("Arial", 12, "bold"), 
                               fg="darkgreen", width=5)
        self.total_label.pack(side=tk.RIGHT)

        # Instructions
        inst_frame = Frame(control_frame)
        inst_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        instructions = """📋 INSTRUCTIONS:
1. Select vehicle filter type
2. Click 'Set Line' 
3. Click 2 points on video
4. Click 'START' to begin
5. Only selected vehicles will be counted"""
        
        Label(inst_frame, text=instructions, 
              font=("Arial", 9), 
              justify=tk.LEFT, 
              wraplength=230,
              bg="lightyellow").pack(fill=tk.X, padx=5, pady=5)

    def on_filter_change(self, event=None):
        """Handle filter dropdown change"""
        selected = self.selected_vehicle_filter.get()
        
        # Update filter status
        if selected == "All Vehicles":
            self.filter_status.config(text="📊 Counting: All vehicles", fg="blue")
        elif selected == "Cars Only":
            self.filter_status.config(text="📊 Counting: Cars only", fg="green")
        elif selected == "Trucks Only":
            self.filter_status.config(text="📊 Counting: Trucks only", fg="orange")
        elif selected == "Motorcycles Only":
            self.filter_status.config(text="📊 Counting: Motorcycles only", fg="purple")
        
        # Update count display visibility
        self.update_count_display_visibility()
        
        print(f"🎯 Filter changed to: {selected}")

    def update_count_display_visibility(self):
        """Update visibility of count displays based on filter"""
        selected = self.selected_vehicle_filter.get()
        
        for vehicle, labels in self.count_labels.items():
            if selected == "All Vehicles":
                # Show all
                labels['frame'].pack(fill=tk.X, pady=3)
            elif selected == "Cars Only" and vehicle == "car":
                labels['frame'].pack(fill=tk.X, pady=3)
            elif selected == "Trucks Only" and vehicle == "truck":
                labels['frame'].pack(fill=tk.X, pady=3)
            elif selected == "Motorcycles Only" and vehicle == "motorcycle":
                labels['frame'].pack(fill=tk.X, pady=3)
            else:
                # Hide this vehicle type
                labels['frame'].pack_forget()

    def should_count_vehicle(self, vehicle_type):
        """Check if vehicle should be counted based on filter"""
        selected = self.selected_vehicle_filter.get()
        
        if selected == "All Vehicles":
            return True
        elif selected == "Cars Only" and vehicle_type == "car":
            return True
        elif selected == "Trucks Only" and vehicle_type == "truck":
            return True
        elif selected == "Motorcycles Only" and vehicle_type == "motorcycle":
            return True
        
        return False

    def update_loop(self):
        """Main update loop - no threading"""
        try:
            # Capture screen
            left = CAPTURE_REGION["left"]
            top = CAPTURE_REGION["top"]
            right = left + CAPTURE_REGION["width"]
            bottom = top + CAPTURE_REGION["height"]
            
            screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            processed_frame = frame.copy()

            # Process if running and line is set
            if self.is_running and len(self.line_points) == 2:
                # Draw counting line
                pt1, pt2 = self.line_points
                cv2.line(processed_frame, pt1, pt2, (0, 0, 255), 3)
                
                # Add line label with filter info
                mid_point = ((pt1[0] + pt2[0]) // 2, (pt1[1] + pt2[1]) // 2)
                filter_text = self.selected_vehicle_filter.get().replace(" Only", "").replace("All Vehicles", "ALL")
                cv2.putText(processed_frame, f"COUNTING LINE ({filter_text})", 
                          (mid_point[0] - 80, mid_point[1] - 10), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

                # YOLO detection with tracking - IMPROVED PARAMETERS
                results = self.model.track(frame, 
                                         persist=True, 
                                         verbose=False,
                                         conf=CONFIDENCE_THRESHOLD,
                                         iou=0.7,  # Lower IoU threshold
                                         max_det=50,  # More detections
                                         classes=[0, 1, 2, 3, 5, 7])  # car, bicycle, motorcycle, airplane, bus, truck

                if results[0].boxes is not None and results[0].boxes.id is not None:
                    boxes = results[0].boxes.xyxy.cpu().numpy().astype(int)
                    ids = results[0].boxes.id.cpu().numpy().astype(int)
                    confs = results[0].boxes.conf.cpu().numpy()
                    clss = results[0].boxes.cls.cpu().numpy().astype(int)

                    for box, track_id, conf, cls_id in zip(boxes, ids, confs, clss):
                        label = self.model.names[cls_id]
                        
                        # Map to vehicle types - EXPANDED DETECTION
                        vehicle_type = None
                        if label in ['car']:
                            vehicle_type = 'car'
                        elif label in ['truck', 'bus']:
                            vehicle_type = 'truck'
                        elif label in ['motorcycle', 'motorbike', 'bicycle']:  # Added bicycle
                            vehicle_type = 'motorcycle'
                        
                        # DEBUG: Print all detected objects
                        if vehicle_type:
                            print(f"🔍 Detected: {label} -> {vehicle_type} (conf: {conf:.2f})")
                        
                        if vehicle_type:
                            x1, y1, x2, y2 = box
                            
                            # Check if this vehicle should be processed based on filter
                            should_process = self.should_count_vehicle(vehicle_type)
                            
                            # Color coding based on filter and counting status
                            if not should_process:
                                color = (100, 100, 100)  # Dark gray for filtered out
                                status = "FILTERED"
                            elif track_id in self.counted_ids:
                                color = (128, 128, 128)  # Gray for counted
                                status = "COUNTED"
                            else:
                                color = (0, 255, 0)  # Green for new
                                status = "NEW"
                            
                            # Draw bounding box
                            cv2.rectangle(processed_frame, (x1, y1), (x2, y2), color, 2)
                            
                            # Draw center point
                            center_x = (x1 + x2) // 2
                            center_y = (y1 + y2) // 2
                            cv2.circle(processed_frame, (center_x, center_y), 5, color, -1)
                            
                            # Label with info
                            label_text = f"{vehicle_type} {conf:.2f} [{status}]"
                            cv2.putText(processed_frame, label_text,
                                      (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                                      0.5, color, 2)

                            # Check line crossing only for vehicles that should be counted
                            if should_process and track_id not in self.counted_ids:
                                if self.check_line_crossing((center_x, center_y), pt1, pt2):
                                    self.vehicle_counts[vehicle_type] += 1
                                    self.counted_ids.add(track_id)
                                    print(f"✅ Counted: {vehicle_type} (ID: {track_id}) [Filter: {self.selected_vehicle_filter.get()}]")
                                    self.update_count_display()

            # Draw line setting points
            if self.is_setting_line:
                for i, point in enumerate(self.line_points):
                    cv2.circle(processed_frame, point, 8, (0, 255, 255), -1)
                    cv2.putText(processed_frame, f"P{i+1}", 
                              (point[0] + 15, point[1]), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                
                if len(self.line_points) == 1:
                    cv2.putText(processed_frame, "Click second point", 
                              (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                              0.7, (0, 255, 255), 2)

            # Update display
            self.update_canvas(processed_frame)
            self.update_fps()
            
        except Exception as e:
            print(f"Update error: {e}")
        
        # Schedule next update (targeting ~30 FPS)
        self.root.after(33, self.update_loop)

    def update_canvas(self, frame):
        """Update canvas with processed frame"""
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        img_tk = ImageTk.PhotoImage(image=img_pil)
        
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
        self.canvas.image = img_tk

    def update_fps(self):
        """Update FPS counter"""
        self.fps_counter += 1
        current_time = time.time()
        
        if current_time - self.last_fps_time >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.last_fps_time = current_time
            self.fps_label.config(text=f"FPS: {self.current_fps}")

    def update_count_display(self):
        """Update count labels"""
        total = 0
        for vehicle, labels in self.count_labels.items():
            count = self.vehicle_counts[vehicle]
            labels['count'].config(text=str(count))
            total += count
        self.total_label.config(text=str(total))

    def toggle_counting(self):
        """Start/stop counting"""
        if not self.is_running:
            if len(self.line_points) < 2:
                messagebox.showwarning("Warning", "Please set counting line first!\nClick 'Set Line' and then click 2 points on the video.")
                return
            
            self.is_running = True
            self.status_label.config(text="● RUNNING", fg="green")
            self.start_btn.config(text="⏸ STOP", bg="lightcoral", fg="darkred")
            self.counted_ids.clear()
            filter_info = self.selected_vehicle_filter.get()
            print(f"🚀 Detection started! Filter: {filter_info}")
        else:
            self.is_running = False
            self.status_label.config(text="● STOPPED", fg="red")
            self.start_btn.config(text="▶ START", bg="lightgreen", fg="darkgreen")
            print("⏹ Detection stopped!")

    def set_line_mode(self):
        """Enter line setting mode"""
        if self.is_running:
            messagebox.showwarning("Warning", "Please stop detection first!")
            return
        
        self.is_setting_line = True
        self.line_points = []
        self.status_label.config(text="● SET LINE MODE", fg="blue")
        messagebox.showinfo("Set Line", "Click 2 points on the video to set counting line.\n\nTip: Draw line across the path where vehicles will pass.")

    def reset_counts(self):
        """Reset all counters"""
        self.vehicle_counts = {'car': 0, 'truck': 0, 'motorcycle': 0}
        self.counted_ids.clear()
        self.update_count_display()
        print("🔄 Counters reset!")

    def on_mouse_click(self, event):
        """Handle mouse clicks for line setting"""
        if self.is_setting_line:
            self.line_points.append((event.x, event.y))
            print(f"Point {len(self.line_points)}: ({event.x}, {event.y})")
            
            if len(self.line_points) == 2:
                self.is_setting_line = False
                self.status_label.config(text="● LINE SET", fg="black")
                print(f"✅ Counting line set: {self.line_points[0]} -> {self.line_points[1]}")
                messagebox.showinfo("Success", "Counting line has been set!\nNow you can click START to begin detection.")

    def check_line_crossing(self, center, pt1, pt2):
        """Check if point crosses the counting line"""
        # Calculate distance from point to line
        x0, y0 = center
        x1, y1 = pt1
        x2, y2 = pt2
        
        # Line equation: Ax + By + C = 0
        A = y2 - y1
        B = x1 - x2
        C = x2 * y1 - x1 * y2
        
        # Distance from point to line
        if A == 0 and B == 0:
            return False
            
        distance = abs(A * x0 + B * y0 + C) / np.sqrt(A*A + B*B)
        
        # Check if point is close to line
        if distance < 25:  # Tolerance
            # Check if point is within line segment bounds (with margin)
            min_x = min(x1, x2) - 30
            max_x = max(x1, x2) + 30
            min_y = min(y1, y2) - 30
            max_y = max(y1, y2) + 30
            
            if min_x <= x0 <= max_x and min_y <= y0 <= max_y:
                return True
        
        return False

    def on_closing(self):
        """Handle window closing"""
        if messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
            print("👋 Closing application...")
            self.root.destroy()

if __name__ == "__main__":
    print("🚗 Starting Simple Vehicle Counter with Filter")
    print("💡 Optimized for AMD Ryzen 5 + Radeon RX")
    print("📋 Make sure YOLO model is at: yolo-Weights/yolo11n.pt")
    print("🎯 New Feature: Vehicle type filtering!")
    
    root = tk.Tk()
    app = SimpleVehicleCounter(root)
    root.mainloop()