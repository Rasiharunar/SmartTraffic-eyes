#Atur DB di line 264

import cv2
import numpy as np
from ultralytics import YOLO
import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
from PIL import Image, ImageTk, ImageGrab
import threading
import time
from collections import defaultdict
import math
import pyautogui
import json
import psycopg2 # Import for PostgreSQL operations
import datetime # Import for handling timestamps

class LineSettingsDialog:
    def __init__(self, parent, current_settings=None):
        self.parent = parent
        self.result = None
        
        # Default settings
        self.settings = {
            'line_color': '#FF0000',
            'line_thickness': 3,
            'line_style': 'solid',
            'show_label': True,
            'label_text': 'COUNTING LINE',
            'detection_threshold': 20,
            'line_type': 'manual'  # manual, horizontal, vertical
        }
        
        if current_settings:
            self.settings.update(current_settings)
            
        self.create_dialog()
        
    def create_dialog(self):
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Line Settings")
        self.dialog.geometry("400x500")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 50,
            self.parent.winfo_rooty() + 50
        ))
        
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Line Type
        type_frame = ttk.LabelFrame(main_frame, text="Line Type", padding=10)
        type_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.line_type_var = tk.StringVar(value=self.settings['line_type'])
        ttk.Radiobutton(type_frame, text="Manual Draw", variable=self.line_type_var, 
                        value="manual").pack(anchor=tk.W)
        ttk.Radiobutton(type_frame, text="Horizontal Line", variable=self.line_type_var, 
                        value="horizontal").pack(anchor=tk.W)
        ttk.Radiobutton(type_frame, text="Vertical Line", variable=self.line_type_var, 
                        value="vertical").pack(anchor=tk.W)
        
        # Appearance
        appearance_frame = ttk.LabelFrame(main_frame, text="Appearance", padding=10)
        appearance_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Color
        color_frame = ttk.Frame(appearance_frame)
        color_frame.pack(fill=tk.X, pady=2)
        ttk.Label(color_frame, text="Color:").pack(side=tk.LEFT)
        
        self.color_var = tk.StringVar(value=self.settings['line_color'])
        self.color_button = tk.Button(color_frame, text="   ", width=3,
                                       bg=self.settings['line_color'],
                                       command=self.choose_color)
        self.color_button.pack(side=tk.RIGHT)
        
        # Thickness
        thickness_frame = ttk.Frame(appearance_frame)
        thickness_frame.pack(fill=tk.X, pady=2)
        ttk.Label(thickness_frame, text="Thickness:").pack(side=tk.LEFT)
        
        self.thickness_var = tk.IntVar(value=self.settings['line_thickness'])
        thickness_spin = ttk.Spinbox(thickness_frame, from_=1, to=10, width=10,
                                     textvariable=self.thickness_var)
        thickness_spin.pack(side=tk.RIGHT)
        
        # Style
        style_frame = ttk.Frame(appearance_frame)
        style_frame.pack(fill=tk.X, pady=2)
        ttk.Label(style_frame, text="Style:").pack(side=tk.LEFT)
        
        self.style_var = tk.StringVar(value=self.settings['line_style'])
        style_combo = ttk.Combobox(style_frame, textvariable=self.style_var,
                                   values=['solid', 'dashed', 'dotted'], width=10)
        style_combo.pack(side=tk.RIGHT)
        
        # Label Settings
        label_frame = ttk.LabelFrame(main_frame, text="Label", padding=10)
        label_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.show_label_var = tk.BooleanVar(value=self.settings['show_label'])
        ttk.Checkbutton(label_frame, text="Show Label", 
                        variable=self.show_label_var).pack(anchor=tk.W)
        
        text_frame = ttk.Frame(label_frame)
        text_frame.pack(fill=tk.X, pady=5)
        ttk.Label(text_frame, text="Text:").pack(side=tk.LEFT)
        
        self.label_text_var = tk.StringVar(value=self.settings['label_text'])
        ttk.Entry(text_frame, textvariable=self.label_text_var).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # Detection Settings
        detection_frame = ttk.LabelFrame(main_frame, text="Detection", padding=10)
        detection_frame.pack(fill=tk.X, pady=(0, 10))
        
        threshold_frame = ttk.Frame(detection_frame)
        threshold_frame.pack(fill=tk.X, pady=2)
        ttk.Label(threshold_frame, text="Detection Threshold:").pack(side=tk.LEFT)
        
        self.threshold_var = tk.IntVar(value=self.settings['detection_threshold'])
        threshold_spin = ttk.Spinbox(threshold_frame, from_=5, to=100, width=10,
                                     textvariable=self.threshold_var)
        threshold_spin.pack(side=tk.RIGHT)
        
        ttk.Label(detection_frame, text="(Distance in pixels for crossing detection)",
                  font=("Arial", 8)).pack()
        
        # Preset Buttons
        preset_frame = ttk.LabelFrame(main_frame, text="Presets", padding=10)
        preset_frame.pack(fill=tk.X, pady=(0, 10))
        
        preset_buttons_frame = ttk.Frame(preset_frame)
        preset_buttons_frame.pack()
        
        ttk.Button(preset_buttons_frame, text="Red Line", 
                   command=lambda: self.apply_preset('red')).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_buttons_frame, text="Blue Line", 
                   command=lambda: self.apply_preset('blue')).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_buttons_frame, text="Green Line", 
                   command=lambda: self.apply_preset('green')).pack(side=tk.LEFT, padx=2)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Reset", command=self.reset_clicked).pack(side=tk.LEFT)
        
    def choose_color(self):
        color = colorchooser.askcolor(initialcolor=self.color_var.get())
        if color[1]:  # If user didn't cancel
            self.color_var.set(color[1])
            self.color_button.config(bg=color[1])
            
    def apply_preset(self, preset_type):
        presets = {
            'red': {'line_color': '#FF0000', 'line_thickness': 3, 'line_style': 'solid'},
            'blue': {'line_color': '#0000FF', 'line_thickness': 2, 'line_style': 'dashed'},
            'green': {'line_color': '#00FF00', 'line_thickness': 4, 'line_style': 'solid'}
        }
        
        if preset_type in presets:
            preset = presets[preset_type]
            self.color_var.set(preset['line_color'])
            self.color_button.config(bg=preset['line_color'])
            self.thickness_var.set(preset['line_thickness'])
            self.style_var.set(preset['line_style'])
            
    def reset_clicked(self):
        self.color_var.set('#FF0000')
        self.color_button.config(bg='#FF0000')
        self.thickness_var.set(3)
        self.style_var.set('solid')
        self.show_label_var.set(True)
        self.label_text_var.set('COUNTING LINE')
        self.threshold_var.set(20)
        self.line_type_var.set('manual')
        
    def ok_clicked(self):
        self.result = {
            'line_color': self.color_var.get(),
            'line_thickness': self.thickness_var.get(),
            'line_style': self.style_var.get(),
            'show_label': self.show_label_var.get(),
            'label_text': self.label_text_var.get(),
            'detection_threshold': self.threshold_var.get(),
            'line_type': self.line_type_var.get()
        }
        self.dialog.destroy()
        
    def cancel_clicked(self):
        self.result = None
        self.dialog.destroy()

class ScreenVehicleCounter:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("YOLO Vehicle Counter - Screen Capture v2.2 FIXED")
        self.root.geometry("1400x900")
        
        # Initialize YOLO model
        try:
            self.model = YOLO('yolov8n.pt')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load YOLO model: {e}. Please ensure you have ultralytics installed.")
            return
        
        # Vehicle classes in COCO dataset
        self.vehicle_classes = [2, 3, 5, 7]  # car, motorcycle, bus, truck
        self.class_names = {2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'}
        
        # Screen capture
        self.capture_region = None
        self.is_capturing = False
        self.is_previewing = False
        self.selecting_region = False
        
        # Counting line with settings - FIXED: Better line tracking
        self.counting_line = None
        self.line_drawn = False
        self.drawing_line = False
        self.line_draw_enabled = False  # NEW: Track if drawing is enabled
        self.line_start = None
        self.line_settings = {
            'line_color': '#FF0000',
            'line_thickness': 3,
            'line_style': 'solid',
            'show_label': True,
            'label_text': 'COUNTING LINE',
            'detection_threshold': 20,
            'line_type': 'manual'
        }
        
        # Tracking
        self.tracked_vehicles = {}
        self.next_id = 0
        self.counted_ids = set()
        self.vehicle_count = defaultdict(int)
        self.total_count = 0
        
        # Frame processing
        self.current_frame = None
        self.capture_thread = None
        self.preview_thread = None

        # Database setup for PostgreSQL
        self.db_conn = None
        self.cursor = None
        self._init_database()
        self.last_db_save_time = time.time()
        self.db_save_interval = 30 # Save data every 30 seconds (in seconds)
        
        # GUI setup
        self.setup_gui()
        
        # Set up a protocol for closing the window to ensure database connection is closed
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def _init_database(self):
        """Initializes the PostgreSQL database connection and creates the table if it doesn't exist."""
        try:
            # --- KONFIGURASI DATABASE POSTGRESQL ---
            # Ganti dengan detail koneksi PostgreSQL Anda
            self.db_conn = psycopg2.connect(
                dbname="smart_tf",   
                user="postgres",      
                password="1234",  
                host="localhost",         
                port="5432"   # default 5432
            )
            self.cursor = self.db_conn.cursor()
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS deteksi_kendaraan (
                    id SERIAL PRIMARY KEY,
                    motor INTEGER NOT NULL,
                    mobil INTEGER NOT NULL,
                    truk INTEGER NOT NULL,
                    bus INTEGER NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            self.db_conn.commit()
            print("Database 'deteksi_kendaraan' (PostgreSQL) initialized successfully.")
        except psycopg2.Error as e:
            messagebox.showerror("Database Error", f"Failed to initialize PostgreSQL database: {e}\n"
                                                  "Please check your connection details and ensure PostgreSQL is running.")
            print(f"PostgreSQL database initialization error: {e}")

    def save_counts_to_db(self):
        """Saves the current vehicle counts to the database."""
        if not self.db_conn:
            print("Database connection not established.")
            return

        motor_count = self.vehicle_count['motorcycle']
        mobil_count = self.vehicle_count['car']
        truk_count = self.vehicle_count['truck']
        bus_count = self.vehicle_count['bus']
        
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            self.cursor.execute('''
                INSERT INTO deteksi_kendaraan (motor, mobil, truk, bus, timestamp)
                VALUES (%s, %s, %s, %s, %s);
            ''', (motor_count, mobil_count, truk_count, bus_count, current_time))
            self.db_conn.commit()
            print(f"Saved counts to DB: Motor={motor_count}, Mobil={mobil_count}, Truk={truk_count}, Bus={bus_count} at {current_time}")
            self.last_db_save_time = time.time() # Reset timer
        except psycopg2.Error as e:
            print(f"Error saving counts to PostgreSQL database: {e}")
            # Rollback in case of error
            if self.db_conn:
                self.db_conn.rollback()

    def on_closing(self):
        """Handles actions when the main window is closed."""
        if self.is_capturing:
            self.is_capturing = False # Stop the capture loop gracefully
            if self.capture_thread and self.capture_thread.is_alive():
                # Give the thread a moment to finish, but don't block indefinitely
                self.capture_thread.join(timeout=1) 
        if self.is_previewing:
            self.is_previewing = False # Stop the preview loop
            if self.preview_thread and self.preview_thread.is_alive():
                self.preview_thread.join(timeout=1)

        # Close database connection
        if self.db_conn:
            try:
                self.db_conn.close()
                print("PostgreSQL database connection closed.")
            except psycopg2.Error as e:
                print(f"Error closing PostgreSQL database connection: {e}")

        self.root.destroy()

    def setup_gui(self):
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Control frame
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))
        
        # Screen capture controls
        capture_group = ttk.LabelFrame(control_frame, text="Screen Capture", padding=10)
        capture_group.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(capture_group, text="Select Region", command=self.select_screen_region).pack(side=tk.LEFT, padx=5)
        ttk.Button(capture_group, text="Full Screen", command=self.capture_full_screen).pack(side=tk.LEFT, padx=5)
        
        # Preview control
        self.preview_button = ttk.Button(capture_group, text="Start Preview", command=self.toggle_preview, state='disabled')
        self.preview_button.pack(side=tk.LEFT, padx=5)
        
        # Line controls
        line_group = ttk.LabelFrame(control_frame, text="Counting Line", padding=10)
        line_group.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(line_group, text="Line Settings", command=self.open_line_settings).pack(side=tk.LEFT, padx=5)
        self.draw_line_button = ttk.Button(line_group, text="Draw Line", command=self.enable_line_drawing)
        self.draw_line_button.pack(side=tk.LEFT, padx=5)
        ttk.Button(line_group, text="Clear Line", command=self.clear_line).pack(side=tk.LEFT, padx=5)
        
        # Control buttons
        control_group = ttk.LabelFrame(control_frame, text="Detection Controls", padding=10)
        control_group.pack(side=tk.LEFT, padx=(0, 10))
        
        self.start_button = ttk.Button(control_group, text="Start Detection", command=self.toggle_capture)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_group, text="Reset Count", command=self.reset_count).pack(side=tk.LEFT, padx=5)
        
        # Status
        status_group = ttk.LabelFrame(control_frame, text="Status", padding=10)
        status_group.pack(side=tk.LEFT)
        
        self.status_label = ttk.Label(status_group, text="Ready - Select a region first")
        self.status_label.pack()
        
        # Content frame
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Video frame
        self.video_frame = ttk.LabelFrame(content_frame, text="Video Feed - Preview Mode", padding=5)
        self.video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.canvas = tk.Canvas(self.video_frame, bg='black', width=800, height=600)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Instructions
        self.instructions = ttk.Label(self.video_frame, text="1. Select region → 2. Preview will start → 3. Setup line → 4. Start detection", 
                                 font=("Arial", 9))
        self.instructions.pack(pady=5)
        
        # Bind mouse events for line drawing - FIXED: Better event handling
        self.canvas.bind("<Button-1>", self.start_line)
        self.canvas.bind("<B1-Motion>", self.draw_line_preview)
        self.canvas.bind("<ButtonRelease-1>", self.end_line)
        
        # Statistics frame
        stats_frame = ttk.LabelFrame(content_frame, text="Vehicle Statistics", padding=10)
        stats_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Count displays
        count_frame = ttk.Frame(stats_frame)
        count_frame.pack(fill=tk.X, pady=10)
        
        self.total_label = ttk.Label(count_frame, text="Total: 0", font=("Arial", 16, "bold"))
        self.total_label.pack(pady=5)
        
        ttk.Separator(count_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        self.car_label = ttk.Label(count_frame, text="Cars: 0", font=("Arial", 12))
        self.car_label.pack(pady=2)
        
        self.motorcycle_label = ttk.Label(count_frame, text="Motorcycles: 0", font=("Arial", 12))
        self.motorcycle_label.pack(pady=2)
        
        self.bus_label = ttk.Label(count_frame, text="Buses: 0", font=("Arial", 12))
        self.bus_label.pack(pady=2)
        
        self.truck_label = ttk.Label(count_frame, text="Trucks: 0", font=("Arial", 12))
        self.truck_label.pack(pady=2)
        
        ttk.Separator(count_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Status indicators
        self.line_status = ttk.Label(count_frame, text="Line: Not drawn", font=("Arial", 10))
        self.line_status.pack(pady=5)
        
        self.region_status = ttk.Label(count_frame, text="Region: Not selected", font=("Arial", 10))
        self.region_status.pack(pady=5)
        
        self.preview_status = ttk.Label(count_frame, text="Preview: Off", font=("Arial", 10))
        self.preview_status.pack(pady=5)
        
        # Real-time info
        info_frame = ttk.LabelFrame(stats_frame, text="Real-time Info", padding=5)
        info_frame.pack(fill=tk.X, pady=10)
        
        self.fps_label = ttk.Label(info_frame, text="FPS: 0", font=("Arial", 9))
        self.fps_label.pack()
        
        self.detection_label = ttk.Label(info_frame, text="Detections: 0", font=("Arial", 9))
        self.detection_label.pack()
        
        # Line info
        line_info_frame = ttk.LabelFrame(stats_frame, text="Line Configuration", padding=5)
        line_info_frame.pack(fill=tk.X, pady=10)
        
        self.line_info_label = ttk.Label(line_info_frame, text="Type: Manual\nColor: Red\nThickness: 3", 
                                         font=("Arial", 8), justify=tk.LEFT)
        self.line_info_label.pack()
        
        # Debug info - FIXED: Added debug info
        debug_frame = ttk.LabelFrame(stats_frame, text="Debug Info", padding=5)
        debug_frame.pack(fill=tk.X, pady=10)
        
        self.debug_label = ttk.Label(debug_frame, text="Draw Mode: Off\nLine Ready: No", 
                                     font=("Arial", 8), justify=tk.LEFT)
        self.debug_label.pack()
        
    def update_debug_info(self):
        """Update debug information display"""
        draw_mode = "On" if self.line_draw_enabled else "Off"
        line_ready = "Yes" if self.line_drawn else "No"
        capturing = "Yes" if self.is_capturing else "No"
        previewing = "Yes" if self.is_previewing else "No"
        
        debug_text = f"Draw Mode: {draw_mode}\nLine Ready: {line_ready}\nCapturing: {capturing}\nPreviewing: {previewing}"
        self.debug_label.config(text=debug_text)
        
    def select_screen_region(self):
        """Allow user to select a screen region by clicking and dragging"""
        self.root.withdraw()  # Hide main window
        time.sleep(0.5)  # Give time for window to hide
        
        try:
            # Create overlay window for region selection
            overlay = tk.Toplevel()
            overlay.attributes('-fullscreen', True)
            overlay.attributes('-alpha', 0.3)
            overlay.configure(bg='black')
            overlay.attributes('-topmost', True)
            
            canvas = tk.Canvas(overlay, highlightthickness=0)
            canvas.pack(fill=tk.BOTH, expand=True)
            
            # Instructions
            canvas.create_text(overlay.winfo_screenwidth()//2, 50, 
                              text="Click and drag to select region, ESC to cancel", 
                              fill='white', font=('Arial', 16))
            
            start_pos = None
            selection_rect = None
            
            def start_selection(event):
                nonlocal start_pos, selection_rect
                start_pos = (event.x, event.y)
                if selection_rect:
                    canvas.delete(selection_rect)
            
            def drag_selection(event):
                nonlocal selection_rect
                if start_pos:
                    if selection_rect:
                        canvas.delete(selection_rect)
                    selection_rect = canvas.create_rectangle(
                        start_pos[0], start_pos[1], event.x, event.y,
                        outline='red', width=2
                    )
            
            def end_selection(event):
                if start_pos:
                    x1, y1 = start_pos
                    x2, y2 = event.x, event.y
                    
                    # Ensure proper coordinates
                    left = min(x1, x2)
                    top = min(y1, y2)
                    width = abs(x2 - x1)
                    height = abs(y2 - y1)
                    
                    if width > 50 and height > 50:  # Minimum size
                        self.capture_region = (left, top, left + width, top + height)
                        self.region_status.config(text=f"Region: {width}x{height}")
                        self.status_label.config(text="Region selected - Starting preview...")
                        
                        # Enable preview button
                        self.preview_button.config(state='normal')
                        
                        # Start preview automatically
                        overlay.destroy()
                        self.root.deiconify()
                        self.root.after(500, self.start_preview_automatically)
                        self.update_debug_info()
                        return
                    
                    overlay.destroy()
                    self.root.deiconify()
            
            def cancel_selection(event):
                overlay.destroy()
                self.root.deiconify()
            
            canvas.bind('<Button-1>', start_selection)
            canvas.bind('<B1-Motion>', drag_selection)
            canvas.bind('<ButtonRelease-1>', end_selection)
            overlay.bind('<Escape>', cancel_selection)
            
            canvas.focus_set()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to select region: {str(e)}")
            self.root.deiconify()
    
    def capture_full_screen(self):
        """Set capture region to full screen"""
        screen_width, screen_height = pyautogui.size()
        self.capture_region = (0, 0, screen_width, screen_height)
        self.region_status.config(text=f"Region: Full Screen ({screen_width}x{screen_height})")
        self.status_label.config(text="Full screen selected - Starting preview...")
        
        # Enable preview button
        self.preview_button.config(state='normal')
        
        # Start preview automatically
        self.start_preview_automatically()
        self.update_debug_info()
    
    def start_preview_automatically(self):
        """Start preview automatically after region selection"""
        if not self.is_previewing:
            self.toggle_preview()
    
    def toggle_preview(self):
        """Start or stop preview mode"""
        if not self.capture_region:
            messagebox.showwarning("Warning", "Please select a capture region first")
            return
        
        self.is_previewing = not self.is_previewing
        self.preview_button.config(text="Stop Preview" if self.is_previewing else "Start Preview")
        
        if self.is_previewing:
            self.preview_status.config(text="Preview: On")
            self.video_frame.config(text="Video Feed - Preview Mode")
            self.status_label.config(text="Preview active - Setup your counting line")
            self.instructions.config(text="Preview active! Now setup your counting line and start detection.")
            self.preview_thread = threading.Thread(target=self.preview_loop, daemon=True)
            self.preview_thread.start()
        else:
            self.preview_status.config(text="Preview: Off")
            self.video_frame.config(text="Video Feed - Stopped")
            self.status_label.config(text="Preview stopped")
            self.canvas.delete("all")
            self.canvas.configure(bg='black')
        
        self.update_debug_info()
    
    def preview_loop(self):
        """Preview loop - shows video without detection"""
        fps_counter = 0
        fps_start_time = time.time()
        
        while self.is_previewing and not self.is_capturing:
            try:
                # Capture screen
                frame = self.capture_screen()
                if frame is None:
                    time.sleep(0.1)
                    continue
                
                # Draw counting line if exists (without detection)
                if self.counting_line:
                    self.draw_counting_line(frame)
                
                # Update display
                self.current_frame = frame.copy()
                self.root.after(0, self.update_display)
                
                # Calculate FPS for preview
                fps_counter += 1
                if fps_counter % 10 == 0:
                    current_time = time.time()
                    fps = 10 / (current_time - fps_start_time)
                    fps_start_time = current_time
                    self.root.after(0, lambda f=fps: self.fps_label.config(text=f"Preview FPS: {f:.1f}"))
                
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                print(f"Preview error: {e}")
                time.sleep(0.1)
    
    def open_line_settings(self):
        """Open line settings dialog"""
        dialog = LineSettingsDialog(self.root, self.line_settings)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            self.line_settings.update(dialog.result)
            self.update_line_info_display()
            
            # If line type changed to horizontal or vertical, create line automatically
            if self.capture_region and dialog.result['line_type'] != 'manual':
                self.create_automatic_line()
        
        self.update_debug_info()
                
    def update_line_info_display(self):
        """Update line configuration display"""
        color_name = self.line_settings['line_color']
        line_type = self.line_settings['line_type'].title()
        thickness = self.line_settings['line_thickness']
        
        info_text = f"Type: {line_type}\nColor: {color_name}\nThickness: {thickness}"
        self.line_info_label.config(text=info_text)
        
    def create_automatic_line(self):
        """Create horizontal or vertical line automatically"""
        if not self.capture_region:
            return
            
        region_width = self.capture_region[2] - self.capture_region[0]
        region_height = self.capture_region[3] - self.capture_region[1]
        
        if self.line_settings['line_type'] == 'horizontal':
            # Horizontal line in the middle
            y = region_height // 2
            self.counting_line = [(0, y), (region_width, y)]
        elif self.line_settings['line_type'] == 'vertical':
            # Vertical line in the middle
            x = region_width // 2
            self.counting_line = [(x, 0), (x, region_height)]
            
        self.line_drawn = True
        self.line_status.config(text="Line: Auto-generated")
        self.instructions.config(text="Line created automatically. Ready to start detection!")
        self.update_debug_info()
        
    def enable_line_drawing(self):
        """Enable manual line drawing mode - FIXED"""
        if not self.capture_region:
            messagebox.showwarning("Warning", "Please select a capture region first")
            return
            
        if self.is_capturing:
            messagebox.showwarning("Warning", "Stop detection before drawing a new line")
            return
        
        # FIXED: Properly enable line drawing mode
        self.line_draw_enabled = True
        self.line_settings['line_type'] = 'manual'
        self.draw_line_button.config(text="Drawing Enabled", state='disabled')
        self.update_line_info_display()
        self.instructions.config(text="LINE DRAWING ENABLED: Click and drag on the video to draw counting line")
        self.status_label.config(text="Click and drag on video to draw line")
        self.update_debug_info()
        
    def toggle_capture(self):
        """Start or stop vehicle detection - FIXED"""
        if not self.capture_region:
            messagebox.showwarning("Warning", "Please select a capture region first")
            return
        
        # FIXED: Check if line is properly drawn
        if not self.line_drawn or self.counting_line is None:
            messagebox.showwarning("Warning", "Please draw a counting line first")
            return
            
        self.is_capturing = not self.is_capturing
        self.start_button.config(text="Stop Detection" if self.is_capturing else "Start Detection")
        
        if self.is_capturing:
            # Stop preview when starting detection
            if self.is_previewing:
                self.is_previewing = False
                self.preview_button.config(text="Start Preview")
                self.preview_status.config(text="Preview: Off")
            
            # Disable line drawing when detecting
            self.line_draw_enabled = False
            self.draw_line_button.config(text="Draw Line", state='normal')
            
            self.video_frame.config(text="Video Feed - Detection Mode")
            self.status_label.config(text="Detection active - Counting vehicles...")
            self.capture_thread = threading.Thread(target=self.capture_loop, daemon=True)
            self.capture_thread.start()
        else:
            self.video_frame.config(text="Video Feed - Detection Stopped")
            self.status_label.config(text="Detection stopped")
            # Restart preview automatically
            if self.capture_region:
                self.root.after(500, lambda: self.toggle_preview() if not self.is_previewing else None)
        
        self.update_debug_info()
    
    def capture_screen(self):
        """Capture screen using PIL ImageGrab"""
        try:
            # Use PIL ImageGrab which is more reliable
            screenshot = ImageGrab.grab(bbox=self.capture_region)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            return frame
        except Exception as e:
            print(f"Screen capture error: {e}")
            return None
    
    def capture_loop(self):
        """Main capture and processing loop for detection"""
        fps_counter = 0
        fps_start_time = time.time()
        
        print("Starting capture loop...") # Added for debugging
        while self.is_capturing:
            try:
                # Capture screen
                frame = self.capture_screen()
                print(f"Captured frame dimensions: {frame.shape if frame is not None else 'None'}") # Added for debugging
                if frame is None:
                    time.sleep(0.1)
                    continue
                
                # YOLO detection
                results = self.model(frame, verbose=False) # Changed to False for less console spam, can be True for more debug
                print(f"YOLO raw results count: {len(results[0].boxes) if results and results[0].boxes else 0}") # Added for debugging
                
                # Process detections
                detections = []
                for r in results:
                    boxes = r.boxes
                    if boxes is not None:
                        for box in boxes:
                            cls = int(box.cls[0])
                            conf = float(box.conf[0])
                            print(f"  Raw Detection: Class={cls} ({self.class_names.get(cls, 'N/A')}), Conf={conf:.2f}, BBox={box.xyxy[0].cpu().numpy().astype(int)}") # Added for debugging
                            if cls in self.vehicle_classes:
                                if conf > 0.2:  # Confidence threshold
                                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                                    detections.append({
                                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                                        'class': cls,
                                        'confidence': conf
                                    })
                print(f"Filtered vehicle detections for tracking: {len(detections)}") # Added for debugging
                
                # Update tracking
                self.update_tracking(detections)
                
                # Draw visualizations
                self.draw_detections(frame, detections)
                self.draw_counting_line(frame)
                
                # Check line crossings
                self.check_line_crossings()
                
                # Periodically save counts to database
                if time.time() - self.last_db_save_time >= self.db_save_interval:
                    self.root.after(0, self.save_counts_to_db) # Schedule save on main thread

                # Update display
                self.current_frame = frame.copy()
                self.root.after(0, self.update_display)
                
                # Calculate FPS
                fps_counter += 1
                if fps_counter % 10 == 0:
                    current_time = time.time()
                    fps = 10 / (current_time - fps_start_time)
                    fps_start_time = current_time
                    self.root.after(0, lambda f=fps: self.fps_label.config(text=f"Detection FPS: {f:.1f}"))
                    self.root.after(0, lambda d=len(detections): self.detection_label.config(text=f"Detections: {d}"))
                
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                print(f"Capture error: {e}")
                time.sleep(0.1)
    
    def update_tracking(self, detections):
        """Update vehicle tracking"""
        max_distance = 100
        updated_tracks = {}
        
        for detection in detections:
            bbox = detection['bbox']
            center = [(bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2]
            
            best_match = None
            best_distance = max_distance
            
            for track_id, track in self.tracked_vehicles.items():
                if track['class'] == detection['class']:
                    distance = math.sqrt(
                        (center[0] - track['center'][0])**2 + 
                        (center[1] - track['center'][1])**2
                    )
                    if distance < best_distance:
                        best_distance = distance
                        best_match = track_id
            
            if best_match is not None:
                updated_tracks[best_match] = {
                    'center': center,
                    'bbox': bbox,
                    'class': detection['class'],
                    'last_seen': time.time(),
                    'path': self.tracked_vehicles[best_match]['path'] + [center]
                }
                # print(f"Track {best_match} updated: {center}") 
            else:
                updated_tracks[self.next_id] = {
                    'center': center,
                    'bbox': bbox,
                    'class': detection['class'],
                    'last_seen': time.time(),
                    'path': [center]
                }
                # print(f"New track {self.next_id} created: {center}") 
                self.next_id += 1
                
        # Remove old tracks
        current_time = time.time()
        self.tracked_vehicles = {
            tid: track for tid, track in updated_tracks.items() 
            if current_time - track['last_seen'] < 1 # Keep tracks for 1 second
        }
        # print(f"Active tracks: {len(self.tracked_vehicles)}") 
        
    def check_line_crossings(self):
        """Check if any tracked vehicles cross the counting line"""
        if not self.line_drawn or self.counting_line is None:
            # print("Line not drawn or missing.") 
            return
            
        line_p1 = np.array(self.counting_line[0])
        line_p2 = np.array(self.counting_line[1])
        
        threshold = self.line_settings['detection_threshold']
        # print(f"Checking crossings with threshold: {threshold}") 
        
        for track_id, track in list(self.tracked_vehicles.items()): # Iterate over a copy
            # print(f"Processing track_id: {track_id}") 
            if track_id in self.counted_ids:
                # print(f"Track {track_id} already counted. Skipping.") 
                continue
            
            # Get current and previous position (if available)
            current_pos = np.array(track['center'])
            
            if len(track['path']) < 2:
                # print(f"Track {track_id} path too short ({len(track['path'])}). Skipping.") 
                continue # Need at least two points to determine direction
                
            prev_pos = np.array(track['path'][-2])
            
            # Vector from line_p1 to current_pos
            vec_p1_current = current_pos - line_p1
            # Vector from line_p1 to prev_pos
            vec_p1_prev = prev_pos - line_p1
            
            # Vector of the line itself
            vec_line = line_p2 - line_p1
            
            # Cross products to determine on which side of the line the points are
            # This is the core logic for line crossing detection
            cross_product_current = np.cross(vec_line, vec_p1_current)
            cross_product_prev = np.cross(vec_line, vec_p1_prev)
            
            print(f"Track {track_id}: prev_pos={prev_pos}, current_pos={current_pos}") 
            print(f"Cross products: current={cross_product_current}, prev={cross_product_prev}") 

            # Check if current and previous points are on opposite sides of the line
            if (cross_product_current * cross_product_prev < 0):
                print(f"Track {track_id} potentially crossed line (opposite sides detected).") 
                # Calculate distance from the current position to the line segment
                line_len_sq = np.sum((line_p2 - line_p1)**2)
                if line_len_sq == 0: # Line is a point
                    dist_to_line = np.linalg.norm(current_pos - line_p1)
                else:
                    # Project point onto the line segment to find the closest point
                    t = max(0, min(1, np.dot(current_pos - line_p1, line_p2 - line_p1) / line_len_sq))
                    projection = line_p1 + t * (line_p2 - line_p1)
                    dist_to_line = np.linalg.norm(current_pos - projection)

                print(f"Track {track_id}: Distance to line = {dist_to_line:.2f}") 

                if dist_to_line < threshold: # If close enough to the line
                    vehicle_type = self.class_names.get(track['class'], 'unknown')
                    self.vehicle_count[vehicle_type] += 1
                    self.total_count += 1
                    self.counted_ids.add(track_id)
                    print(f"Vehicle {track_id} ({vehicle_type}) *COUNTED*! Total {vehicle_type}: {self.vehicle_count[vehicle_type]}, Total: {self.total_count}") # This will always print on count
                    self.update_count_labels()
                else:
                    print(f"Track {track_id} crossed but too far from line (dist={dist_to_line:.2f} >= threshold={threshold}).") 
            else:
                print(f"Track {track_id} did not cross line (same side).") 
                    
    def update_count_labels(self):
        """Update the count labels in the GUI"""
        self.root.after(0, lambda: self.total_label.config(text=f"Total: {self.total_count}"))
        self.root.after(0, lambda: self.car_label.config(text=f"Cars: {self.vehicle_count['car']}"))
        self.root.after(0, lambda: self.motorcycle_label.config(text=f"Motorcycles: {self.vehicle_count['motorcycle']}"))
        self.root.after(0, lambda: self.bus_label.config(text=f"Buses: {self.vehicle_count['bus']}"))
        self.root.after(0, lambda: self.truck_label.config(text=f"Trucks: {self.vehicle_count['truck']}"))
    
    def reset_count(self):
        """Reset all vehicle counts"""
        if messagebox.askyesno("Reset Counts", "Are you sure you want to reset all vehicle counts?"):
            self.vehicle_count = defaultdict(int)
            self.total_count = 0
            self.counted_ids = set()
            self.tracked_vehicles = {}
            self.next_id = 0
            self.update_count_labels()
            self.status_label.config(text="Counts reset.")
            print("All counts reset.")
            
    def draw_detections(self, frame, detections):
        """Draw bounding boxes and class names on the frame"""
        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            cls_name = self.class_names.get(detection['class'], 'unknown')
            conf = detection['confidence']
            
            # Draw rectangle
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw label
            label = f"{cls_name} {conf:.2f}"
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Draw center dot for tracking
            center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
            cv2.circle(frame, (center_x, center_y), 3, (0, 0, 255), -1)
            
        # Draw tracked vehicle paths
        for track_id, track in self.tracked_vehicles.items():
            path = track['path']
            for i in range(1, len(path)):
                cv2.line(frame, path[i-1], path[i], (255, 0, 0), 1)

    def draw_counting_line(self, frame):
        """Draw the counting line on the frame"""
        if self.counting_line:
            p1 = self.counting_line[0]
            p2 = self.counting_line[1]
            
            # Convert hex color to BGR
            hex_color = self.line_settings['line_color'].lstrip('#')
            rgb_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            bgr_color = (rgb_color[2], rgb_color[1], rgb_color[0]) # OpenCV uses BGR
            
            thickness = self.line_settings['line_thickness']
            style = self.line_settings['line_style']
            
            if style == 'solid':
                cv2.line(frame, p1, p2, bgr_color, thickness)
            else: # For dashed/dotted, draw multiple small segments
                length = int(math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2))
                if length == 0: return

                num_segments = length // (thickness * 2) # Adjust based on thickness
                if num_segments == 0: num_segments = 1
                
                dx = (p2[0] - p1[0]) / num_segments
                dy = (p2[1] - p1[1]) / num_segments
                
                for i in range(num_segments):
                    start_seg_x = int(p1[0] + i * dx)
                    start_seg_y = int(p1[1] + i * dy)
                    end_seg_x = int(p1[0] + (i + 0.5) * dx) # Draw half segment, half gap
                    end_seg_y = int(p1[1] + (i + 0.5) * dy)
                    cv2.line(frame, (start_seg_x, start_seg_y), (end_seg_x, end_seg_y), bgr_color, thickness)
                    
            if self.line_settings['show_label']:
                label_text = self.line_settings['label_text']
                mid_x = (p1[0] + p2[0]) // 2
                mid_y = (p1[1] + p2[1]) // 2
                cv2.putText(frame, label_text, (mid_x + 10, mid_y - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, bgr_color, 2)

    def start_line(self, event):
        """Start drawing the line on canvas"""
        if self.line_draw_enabled:
            self.drawing_line = True
            # Convert canvas coords to frame coords (relative to capture region)
            # This is simplified. Proper conversion would need canvas size vs frame size.
            # Assuming canvas displays actual capture region size
            self.line_start = (event.x, event.y)
            self.canvas.delete("temp_line") # Clear any previous temp line
            
    def draw_line_preview(self, event):
        """Draw a temporary line as user drags"""
        if self.drawing_line and self.line_start:
            self.canvas.delete("temp_line")
            self.canvas.create_line(self.line_start[0], self.line_start[1], 
                                    event.x, event.y, 
                                    fill=self.line_settings['line_color'], 
                                    width=self.line_settings['line_thickness'], 
                                    tags="temp_line")
            
    def end_line(self, event):
        if self.drawing_line and self.line_start:
            self.drawing_line = False
            self.canvas.delete("temp_line")

            # Hitung skala antara canvas dan frame
            if self.current_frame is None:
                return
            frame_h, frame_w = self.current_frame.shape[:2]
            canvas_w = self.canvas.winfo_width()
            canvas_h = self.canvas.winfo_height()

            aspect_ratio = frame_w / frame_h
            canvas_aspect_ratio = canvas_w / canvas_h

            if aspect_ratio > canvas_aspect_ratio:
                scale = frame_w / canvas_w
                offset_x = 0
                offset_y = (canvas_h - (canvas_w / aspect_ratio)) / 2
            else:
                scale = frame_h / canvas_h
                offset_y = 0
                offset_x = (canvas_w - (canvas_h * aspect_ratio)) / 2

            # Koreksi koordinat dari canvas ke koordinat frame asli
            def canvas_to_frame(x, y):
                return int((x - offset_x) * scale), int((y - offset_y) * scale)

            p1_canvas = self.line_start
            p2_canvas = (event.x, event.y)

            p1_frame = canvas_to_frame(*p1_canvas)
            p2_frame = canvas_to_frame(*p2_canvas)

            if math.sqrt((p2_frame[0] - p1_frame[0])**2 + (p2_frame[1] - p1_frame[1])**2) > 10:
                self.counting_line = [p1_frame, p2_frame]
                self.line_drawn = True
                self.line_draw_enabled = False
                self.draw_line_button.config(text="Draw Line", state='normal')
                self.line_status.config(text="Line: Drawn Manually")
                self.instructions.config(text="Counting line drawn! Ready to start detection.")
                self.update_debug_info()
            else:
                messagebox.showwarning("Warning", "Line too short. Please draw a longer line.")
                self.line_drawn = False
                self.line_status.config(text="Line: Not drawn")
            self.line_start = None

            
    def clear_line(self):
        """Clear the counting line"""
        if messagebox.askyesno("Clear Line", "Are you sure you want to clear the counting line?"):
            self.counting_line = None
            self.line_drawn = False
            self.line_status.config(text="Line: Not drawn")
            self.instructions.config(text="Counting line cleared. Please draw a new line or select an automatic one.")
            self.update_debug_info()
            # If detection is running, stop it because no line is set
            if self.is_capturing:
                self.toggle_capture()

    def update_display(self):
        """Update the Tkinter canvas with the current frame"""
        if self.current_frame is not None:
            # Convert OpenCV BGR image to RGB PIL image
            img = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            
            # Resize image to fit canvas while maintaining aspect ratio
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width == 1 and canvas_height == 1: # Initial state before window is fully rendered
                return

            img_width, img_height = img.size
            
            aspect_ratio = img_width / img_height
            canvas_aspect_ratio = canvas_width / canvas_height
            
            if aspect_ratio > canvas_aspect_ratio:
                # Image is wider than canvas
                new_width = canvas_width
                new_height = int(canvas_width / aspect_ratio)
            else:
                # Image is taller than canvas or aspect ratios are similar
                new_height = canvas_height
                new_width = int(canvas_height * aspect_ratio)
            
            img = img.resize((new_width, new_height), Image.LANCZOS)
            
            self.photo = ImageTk.PhotoImage(image=img)
            
            # Clear previous images and draw new one
            self.canvas.delete("all")
            # Center the image on the canvas
            self.canvas.create_image(canvas_width / 2, canvas_height / 2, 
                                     image=self.photo, anchor=tk.CENTER)
            
if __name__ == "__main__":
    app = ScreenVehicleCounter()
    app.root.mainloop()

