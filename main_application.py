"""
Modern UI Vehicle Counter Application - TTK Compatible Version
Updated: 2025-07-31 17:39:32 UTC by Rasiharunar
"""

import cv2
import numpy as np
from ultralytics import YOLO
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageGrab
import threading
import time
import math
import pyautogui

from config import *
from database_handler import DatabaseHandler
from line_settings_dialog import LineSettingsDialog
from vehicle_tracker import VehicleTracker

class ModernScreenVehicleCounter:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🚗 Smart Traffic Counter v3.0 - Modern UI")
        self.root.geometry("1600x1000")
        self.root.configure(bg='#1e1e1e')  # Dark theme
        
        # Initialize components first
        self.init_yolo_model()
        self.init_variables()
        
        # Initialize handlers (with graceful database handling)
        self.db_handler = DatabaseHandler()
        self.vehicle_tracker = VehicleTracker()
        
        # Setup modern GUI (without complex TTK styles)
        self.setup_modern_gui()
        
        # Set up window close protocol
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def init_yolo_model(self):
        """Initialize YOLO model"""
        try:
            self.model = YOLO(MODEL_CONFIG['model_path'])
            print("✅ YOLO model loaded successfully")
        except Exception as e:
            messagebox.showerror("Model Error", f"Failed to load YOLO model: {e}")
            return
    
    def init_variables(self):
        """Initialize application variables"""
        # Screen capture
        self.capture_region = None
        self.is_capturing = False
        self.is_previewing = False
        self.selecting_region = False
        
        # Line settings
        self.counting_line = None
        self.line_drawn = False
        self.drawing_line = False
        self.line_draw_enabled = False
        self.line_start = None
        self.line_settings = DEFAULT_LINE_SETTINGS.copy()
        
        # Frame processing
        self.current_frame = None
        self.capture_thread = None
        self.preview_thread = None

    def setup_modern_gui(self):
        """Setup the modern GUI layout with simple styling"""
        # Main container with modern layout
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        
        # Create main container using tk.Frame for better compatibility
        main_container = tk.Frame(self.root, bg='#2d2d2d')
        main_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_container.rowconfigure(1, weight=1)
        main_container.columnconfigure(1, weight=1)
        
        # Top header bar
        self.create_header_bar(main_container)
        
        # Left sidebar for controls
        self.create_left_sidebar(main_container)
        
        # Center video area
        self.create_center_video_area(main_container)
        
        # Right sidebar for database and stats
        self.create_right_sidebar(main_container)

    def create_header_bar(self, parent):
        """Create modern header bar"""
        header_frame = tk.Frame(parent, bg='#363636', relief='raised', bd=1)
        header_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        
        # App title and logo
        title_frame = tk.Frame(header_frame, bg='#363636')
        title_frame.pack(side=tk.LEFT, padx=15, pady=15)
        
        title_label = tk.Label(title_frame, 
                               text="🚗 Smart Traffic Counter v3.0", 
                               bg='#363636', fg='#00d4ff',
                               font=('Arial', 14, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = tk.Label(title_frame,
                                  text="Real-time Vehicle Detection & Counting with AI",
                                  bg='#363636', fg='#ffffff',
                                  font=('Arial', 10))
        subtitle_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Status indicator
        status_frame = tk.Frame(header_frame, bg='#363636')
        status_frame.pack(side=tk.RIGHT, padx=15, pady=15)
        
        # Database connection status
        db_status_text = "🟢 DB Connected" if self.db_handler.db_conn else "🔴 DB Disconnected"
        self.connection_status = tk.Label(status_frame,
                                          text=db_status_text,
                                          bg='#363636', fg='#ffffff',
                                          font=('Arial', 10))
        self.connection_status.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Date and time
        datetime_label = tk.Label(status_frame,
                                  text="📅 2025-07-31 17:39:32 UTC | 👤 Rasiharunar",
                                  bg='#363636', fg='#ffffff',
                                  font=('Arial', 9))
        datetime_label.pack(side=tk.RIGHT, padx=(0, 20))

    def create_left_sidebar(self, parent):
        """Create left sidebar for main controls"""
        left_frame = tk.Frame(parent, bg='#2d2d2d', width=280)
        left_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        left_frame.grid_propagate(False)
        
        # Screen Capture Section
        capture_card = tk.LabelFrame(left_frame, text="📹 Screen Capture", 
                                    bg='#2d2d2d', fg='#ffffff',
                                    font=('Arial', 10, 'bold'),
                                    relief='solid', bd=1)
        capture_card.pack(fill=tk.X, pady=(0, 15), padx=10)
        
        # Create a frame inside for padding
        capture_inner = tk.Frame(capture_card, bg='#2d2d2d')
        capture_inner.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(capture_inner, text="🎯 Select Region", 
                  command=self.select_screen_region,
                  bg='#0078d4', fg='white',
                  font=('Arial', 9), relief='flat',
                  bd=0, pady=5).pack(fill=tk.X, pady=2)
        
        tk.Button(capture_inner, text="🖥️ Full Screen", 
                  command=self.capture_full_screen,
                  bg='#0078d4', fg='white',
                  font=('Arial', 9), relief='flat',
                  bd=0, pady=5).pack(fill=tk.X, pady=2)
        
        self.preview_button = tk.Button(capture_inner, text="▶️ Start Preview", 
                                        command=self.toggle_preview, 
                                        state='disabled',
                                        bg='#107c10', fg='white',
                                        font=('Arial', 9), relief='flat',
                                        bd=0, pady=5)
        self.preview_button.pack(fill=tk.X, pady=(5, 0))
        
        # Line Configuration Section
        line_card = tk.LabelFrame(left_frame, text="📏 Counting Line Setup", 
                                  bg='#2d2d2d', fg='#ffffff',
                                  font=('Arial', 10, 'bold'),
                                  relief='solid', bd=1)
        line_card.pack(fill=tk.X, pady=(0, 15), padx=10)
        
        line_inner = tk.Frame(line_card, bg='#2d2d2d')
        line_inner.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(line_inner, text="⚙️ Line Settings", 
                  command=self.open_line_settings,
                  bg='#0078d4', fg='white',
                  font=('Arial', 9), relief='flat',
                  bd=0, pady=5).pack(fill=tk.X, pady=2)
        
        self.draw_line_button = tk.Button(line_inner, text="✏️ Draw Line", 
                                          command=self.enable_line_drawing,
                                          bg='#0078d4', fg='white',
                                          font=('Arial', 9), relief='flat',
                                          bd=0, pady=5)
        self.draw_line_button.pack(fill=tk.X, pady=2)
        
        tk.Button(line_inner, text="🗑️ Clear Line", 
                  command=self.clear_line,
                  bg='#d13438', fg='white',
                  font=('Arial', 9), relief='flat',
                  bd=0, pady=5).pack(fill=tk.X, pady=2)
        
        # Detection Control Section
        detection_card = tk.LabelFrame(left_frame, text="🚀 Detection Control", 
                                       bg='#2d2d2d', fg='#ffffff',
                                       font=('Arial', 10, 'bold'),
                                       relief='solid', bd=1)
        detection_card.pack(fill=tk.X, pady=(0, 15), padx=10)
        
        detection_inner = tk.Frame(detection_card, bg='#2d2d2d')
        detection_inner.pack(fill=tk.X, padx=10, pady=10)
        
        self.start_button = tk.Button(detection_inner, text="🎬 Start Detection", 
                                      command=self.toggle_capture,
                                      bg='#107c10', fg='white',
                                      font=('Arial', 9), relief='flat',
                                      bd=0, pady=5)
        self.start_button.pack(fill=tk.X, pady=2)
        
        tk.Button(detection_inner, text="🔄 Reset Counts", 
                  command=self.reset_count,
                  bg='#d13438', fg='white',
                  font=('Arial', 9), relief='flat',
                  bd=0, pady=5).pack(fill=tk.X, pady=(5, 0))
        
        # Status Information
        status_card = tk.LabelFrame(left_frame, text="📊 System Status", 
                                    bg='#2d2d2d', fg='#ffffff',
                                    font=('Arial', 10, 'bold'),
                                    relief='solid', bd=1)
        status_card.pack(fill=tk.X, padx=10)
        
        status_inner = tk.Frame(status_card, bg='#2d2d2d')
        status_inner.pack(fill=tk.X, padx=10, pady=10)
        
        self.region_status = tk.Label(status_inner, text="📺 Region: Not selected", 
                                      bg='#2d2d2d', fg='#ffffff',
                                      font=('Arial', 9))
        self.region_status.pack(anchor=tk.W, pady=1)
        
        self.line_status = tk.Label(status_inner, text="📏 Line: Not drawn", 
                                    bg='#2d2d2d', fg='#ffffff',
                                    font=('Arial', 9))
        self.line_status.pack(anchor=tk.W, pady=1)
        
        self.preview_status = tk.Label(status_inner, text="👁️ Preview: Off", 
                                       bg='#2d2d2d', fg='#ffffff',
                                       font=('Arial', 9))
        self.preview_status.pack(anchor=tk.W, pady=1)

    def create_center_video_area(self, parent):
        """Create center video display area"""
        video_container = tk.Frame(parent, bg='#363636', relief='solid', bd=1)
        video_container.grid(row=1, column=1, sticky="nsew", padx=(0, 10))
        video_container.rowconfigure(1, weight=1)
        video_container.columnconfigure(0, weight=1)
        
        # Video header
        video_header = tk.Frame(video_container, bg='#363636')
        video_header.grid(row=0, column=0, sticky="ew", pady=10, padx=10)
        
        self.video_title = tk.Label(video_header, 
                                    text="🎥 Live Video Feed - Modern AI Detection",
                                    bg='#363636', fg='#00d4ff',
                                    font=('Arial', 14, 'bold'))
        self.video_title.pack(side=tk.LEFT)
        
        # FPS and detection info
        info_frame = tk.Frame(video_header, bg='#363636')
        info_frame.pack(side=tk.RIGHT)
        
        self.fps_label = tk.Label(info_frame, text="📈 FPS: 0", 
                                  bg='#363636', fg='#ffffff',
                                  font=('Arial', 9))
        self.fps_label.pack(side=tk.RIGHT, padx=(0, 15))
        
        self.detection_label = tk.Label(info_frame, text="🎯 Detections: 0", 
                                        bg='#363636', fg='#ffffff',
                                        font=('Arial', 9))
        self.detection_label.pack(side=tk.RIGHT, padx=(0, 15))
        
        # Video canvas with modern styling
        canvas_frame = tk.Frame(video_container, bg='#363636')
        canvas_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        canvas_frame.rowconfigure(0, weight=1)
        canvas_frame.columnconfigure(0, weight=1)
        
        self.canvas = tk.Canvas(canvas_frame, bg='#1a1a1a', highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        # Modern instructions
        instruction_frame = tk.Frame(video_container, bg='#363636')
        instruction_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10), padx=10)
        
        self.instructions = tk.Label(instruction_frame,
                                     text="🟢 Active Vehicle | ⚫ Counted Vehicle | Select region → Preview → Draw line → Start detection",
                                     bg='#363636', fg='#ffffff',
                                     font=('Arial', 9))
        self.instructions.pack()
        
        # Bind mouse events
        self.canvas.bind("<Button-1>", self.start_line)
        self.canvas.bind("<B1-Motion>", self.draw_line_preview)
        self.canvas.bind("<ButtonRelease-1>", self.end_line)

    def create_right_sidebar(self, parent):
        """Create right sidebar for database and statistics"""
        right_frame = tk.Frame(parent, bg='#2d2d2d', width=320)
        right_frame.grid(row=1, column=2, sticky="nsew")
        right_frame.grid_propagate(False)
        
        # Vehicle Count Dashboard
        stats_card = tk.LabelFrame(right_frame, text="📊 Live Statistics Dashboard", 
                                   bg='#2d2d2d', fg='#ffffff',
                                   font=('Arial', 10, 'bold'),
                                   relief='solid', bd=1)
        stats_card.pack(fill=tk.X, pady=(0, 15), padx=10)
        
        # Total counts with modern cards
        total_frame = tk.Frame(stats_card, bg='#363636', relief='solid', bd=1)
        total_frame.pack(fill=tk.X, pady=10, padx=10)
        
        self.total_up_label = tk.Label(total_frame, text="📈 Total UP: 0", 
                                       bg='#363636', fg='#28a745',
                                       font=('Arial', 12, 'bold'))
        self.total_up_label.pack(pady=5)
        
        self.total_down_label = tk.Label(total_frame, text="📉 Total DOWN: 0", 
                                         bg='#363636', fg='#dc3545',
                                         font=('Arial', 12, 'bold'))
        self.total_down_label.pack(pady=5)
        
        # Vehicle type breakdown
        self.create_modern_vehicle_counts(stats_card)
        
        # ====== DATABASE SECTION - RIGHT SIDEBAR ======
        database_card = tk.LabelFrame(right_frame, text="💾 Database Operations", 
                                      bg='#2d2d2d', fg='#ffffff',
                                      font=('Arial', 10, 'bold'),
                                      relief='solid', bd=1)
        database_card.pack(fill=tk.X, pady=(0, 15), padx=10)
        
        # Database status
        db_status_frame = tk.Frame(database_card, bg='#363636', relief='solid', bd=1)
        db_status_frame.pack(fill=tk.X, pady=10, padx=10)
        
        db_status_text = "🔌 Database: Connected" if self.db_handler.db_conn else "❌ Database: Disconnected"
        db_status_color = '#28a745' if self.db_handler.db_conn else '#dc3545'
        self.db_status_label = tk.Label(db_status_frame, 
                                        text=db_status_text,
                                        bg='#363636', fg=db_status_color,
                                        font=('Arial', 9))
        self.db_status_label.pack(pady=5)
        
        # Database controls
        db_inner = tk.Frame(database_card, bg='#2d2d2d')
        db_inner.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(db_inner, text="💾 Save to Database", 
                  command=self.save_counts_to_db,
                  bg='#107c10', fg='white',
                  font=('Arial', 9), relief='flat',
                  bd=0, pady=5).pack(fill=tk.X, pady=2)
        
        tk.Button(db_inner, text="📊 View Reports", 
                  command=self.view_reports,
                  bg='#0078d4', fg='white',
                  font=('Arial', 9), relief='flat',
                  bd=0, pady=5).pack(fill=tk.X, pady=2)
        
        tk.Button(db_inner, text="📤 Export Data", 
                  command=self.export_data,
                  bg='#0078d4', fg='white',
                  font=('Arial', 9), relief='flat',
                  bd=0, pady=5).pack(fill=tk.X, pady=2)
        
        # System Information
        system_card = tk.LabelFrame(right_frame, text="⚙️ System Information", 
                                    bg='#2d2d2d', fg='#ffffff',
                                    font=('Arial', 10, 'bold'),
                                    relief='solid', bd=1)
        system_card.pack(fill=tk.X, pady=(0, 15), padx=10)
        
        system_inner = tk.Frame(system_card, bg='#2d2d2d')
        system_inner.pack(fill=tk.X, padx=10, pady=10)
        
        # Model info
        model_info = tk.Label(system_inner, text="🤖 Model: YOLOv11n", 
                             bg='#2d2d2d', fg='#ffffff',
                             font=('Arial', 9))
        model_info.pack(anchor=tk.W, pady=1)
        
        # Performance info
        performance_frame = tk.Frame(system_inner, bg='#363636', relief='solid', bd=1)
        performance_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(performance_frame, text="Performance Metrics:", 
                 bg='#363636', fg='#ffffff',
                 font=('Arial', 9, 'bold')).pack(anchor=tk.W, padx=5, pady=2)
        
        self.accuracy_label = tk.Label(performance_frame, text="🎯 Accuracy: ~75%", 
                                      bg='#363636', fg='#ffffff',
                                      font=('Arial', 9))
        self.accuracy_label.pack(anchor=tk.W, pady=1, padx=5)
        
        # Direction Legend
        legend_card = tk.LabelFrame(right_frame, text="🧭 Direction Legend", 
                                    bg='#2d2d2d', fg='#ffffff',
                                    font=('Arial', 10, 'bold'),
                                    relief='solid', bd=1)
        legend_card.pack(fill=tk.X, padx=10)
        
        legend_inner = tk.Frame(legend_card, bg='#2d2d2d')
        legend_inner.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(legend_inner, text="📈 ↑ UP/LEFT direction", 
                 bg='#2d2d2d', fg='#28a745',
                 font=('Arial', 8)).pack(anchor=tk.W, pady=1)
        tk.Label(legend_inner, text="📉 ↓ DOWN/RIGHT direction", 
                 bg='#2d2d2d', fg='#dc3545',
                 font=('Arial', 8)).pack(anchor=tk.W, pady=1)
        
        # Color coding
        tk.Label(legend_inner, text="🟢 Active Vehicle", 
                 bg='#2d2d2d', fg='#ffffff',
                 font=('Arial', 8)).pack(anchor=tk.W, pady=1)
        tk.Label(legend_inner, text="⚫ Counted Vehicle", 
                 bg='#2d2d2d', fg='#ffffff',
                 font=('Arial', 8)).pack(anchor=tk.W, pady=1)

    def create_modern_vehicle_counts(self, parent):
        """Create modern vehicle count displays"""
        vehicles = [
            ('🚗 Cars', 'car'),
            ('🏍️ Motorcycles', 'motorcycle'),
            ('🚌 Buses', 'bus'),
            ('🚛 Trucks', 'truck')
        ]
        
        for emoji_name, vehicle_type in vehicles:
            vehicle_frame = tk.Frame(parent, bg='#363636', relief='solid', bd=1)
            vehicle_frame.pack(fill=tk.X, pady=2, padx=10)
            
            # Vehicle type label
            type_label = tk.Label(vehicle_frame, text=emoji_name, 
                                  bg='#363636', fg='#ffffff',
                                  font=('Arial', 10, 'bold'))
            type_label.pack(side=tk.LEFT, padx=10, pady=5)
            
            # Count labels
            count_frame = tk.Frame(vehicle_frame, bg='#363636')
            count_frame.pack(side=tk.RIGHT, padx=10, pady=5)
            
            # Create labels for up and down counts
            up_label = tk.Label(count_frame, text="↑0", 
                               bg='#363636', fg='#28a745',
                               font=('Arial', 10))
            up_label.pack(side=tk.RIGHT, padx=(10, 5))
            
            down_label = tk.Label(count_frame, text="↓0", 
                                 bg='#363636', fg='#dc3545',
                                 font=('Arial', 10))
            down_label.pack(side=tk.RIGHT, padx=5)
            
            # Store references
            setattr(self, f'{vehicle_type}_up_label', up_label)
            setattr(self, f'{vehicle_type}_down_label', down_label)

    # ==================== EVENT HANDLERS ====================
    
    def select_screen_region(self):
        """Allow user to select a screen region with modern overlay"""
        self.root.withdraw()
        time.sleep(0.5)
        
        try:
            overlay = tk.Toplevel()
            overlay.attributes('-fullscreen', True)
            overlay.attributes('-alpha', 0.3)
            overlay.configure(bg='#1a1a1a')
            overlay.attributes('-topmost', True)
            
            canvas = tk.Canvas(overlay, highlightthickness=0, bg='#1a1a1a')
            canvas.pack(fill=tk.BOTH, expand=True)
            
            # Modern instructions
            canvas.create_text(overlay.winfo_screenwidth()//2, 50, 
                              text="🎯 Click and drag to select detection region | ESC to cancel", 
                              fill='#00d4ff', font=('Arial', 18, 'bold'))
            
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
                        outline='#00d4ff', width=3
                    )
            
            def end_selection(event):
                if start_pos:
                    x1, y1 = start_pos
                    x2, y2 = event.x, event.y
                    
                    left = min(x1, x2)
                    top = min(y1, y2)
                    width = abs(x2 - x1)
                    height = abs(y2 - y1)
                    
                    if width > 50 and height > 50:
                        self.capture_region = (left, top, left + width, top + height)
                        self.region_status.config(text=f"📺 Region: {width}×{height}px")
                        
                        self.preview_button.config(state='normal')
                        
                        overlay.destroy()
                        self.root.deiconify()
                        self.root.after(500, self.start_preview_automatically)
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
        self.region_status.config(text=f"📺 Region: Full Screen ({screen_width}×{screen_height})")
        
        self.preview_button.config(state='normal')
        self.start_preview_automatically()

    def start_preview_automatically(self):
        """Start preview automatically after region selection"""
        if not self.is_previewing:
            self.toggle_preview()

    def toggle_preview(self):
        """Start or stop preview mode"""
        if not self.capture_region:
            messagebox.showwarning("⚠️ Warning", "Please select a capture region first")
            return
        
        self.is_previewing = not self.is_previewing
        self.preview_button.config(text="⏹️ Stop Preview" if self.is_previewing else "▶️ Start Preview")
        
        if self.is_previewing:
            self.preview_status.config(text="👁️ Preview: Active", fg='#28a745')
            self.video_title.config(text="🎥 Live Preview - Draw Your Counting Line")
            self.instructions.config(text="🟢 Active Vehicle | ⚫ Counted Vehicle | Draw ONE counting line for directional detection.")
            self.preview_thread = threading.Thread(target=self.preview_loop, daemon=True)
            self.preview_thread.start()
        else:
            self.preview_status.config(text="👁️ Preview: Off", fg='#ffffff')
            self.video_title.config(text="🎥 Live Video Feed - Modern AI Detection")
            self.canvas.delete("all")
            self.canvas.configure(bg='#1a1a1a')

    def preview_loop(self):
        """Preview loop - shows video without detection"""
        fps_counter = 0
        fps_start_time = time.time()
        
        while self.is_previewing and not self.is_capturing:
            try:
                frame = self.capture_screen()
                if frame is None:
                    time.sleep(0.1)
                    continue
                
                if self.counting_line:
                    self.draw_counting_line(frame)

                self.current_frame = frame.copy()
                self.root.after(0, self.update_display)

                fps_counter += 1
                if fps_counter % 10 == 0:
                    current_time = time.time()
                    fps = 10 / (current_time - fps_start_time)
                    fps_start_time = current_time
                    self.root.after(0, lambda f=fps: self.fps_label.config(text=f"📈 Preview FPS: {f:.1f}"))

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
            
            if self.capture_region and dialog.result['line_type'] != 'manual':
                self.create_automatic_line()

    def create_automatic_line(self):
        """Create horizontal or vertical line automatically"""
        if not self.capture_region:
            return
            
        region_width = self.capture_region[2] - self.capture_region[0]
        region_height = self.capture_region[3] - self.capture_region[1]
        
        if self.line_settings['line_type'] == 'horizontal':
            y = region_height // 2
            self.counting_line = [(0, y), (region_width, y)]
        elif self.line_settings['line_type'] == 'vertical':
            x = region_width // 2
            self.counting_line = [(x, 0), (x, region_height)]
            
        self.line_drawn = True
        self.line_status.config(text="📏 Line: Auto-generated")
        self.instructions.config(text="✅ Line created automatically. Ready to start detection!")

    def enable_line_drawing(self):
        """Enable manual line drawing mode for single line"""
        if not self.capture_region:
            messagebox.showwarning("⚠️ Warning", "Please select a capture region first")
            return
        if self.is_capturing:
            messagebox.showwarning("⚠️ Warning", "Stop detection before drawing a new line")
            return
        
        self.line_draw_enabled = True
        self.line_settings['line_type'] = 'manual'
        self.draw_line_button.config(text="✏️ Drawing Enabled", state='disabled')
        self.instructions.config(text="✏️ LINE DRAWING ENABLED: Click and drag on the video to create ONE counting line.")

    def clear_line(self):
        """Clear the counting line"""
        if messagebox.askyesno("🗑️ Clear Line", "Are you sure you want to clear the counting line?"):
            self.counting_line = None
            self.line_drawn = False
            self.line_status.config(text="📏 Line: Not drawn")
            self.instructions.config(text="🚫 Counting line cleared. Draw a new line for directional detection.")
            if self.is_capturing:
                self.toggle_capture()

    def toggle_capture(self):
        """Start or stop vehicle detection"""
        if not self.capture_region:
            messagebox.showwarning("⚠️ Warning", "Please select a capture region first")
            return

        if not self.is_capturing:
            if not self.line_drawn or not self.counting_line:
                messagebox.showwarning("⚠️ Warning", "Please draw a counting line first")
                return

        self.is_capturing = not self.is_capturing
        self.start_button.config(text="⏹️ Stop Detection" if self.is_capturing else "🎬 Start Detection")

        if self.is_capturing:
            if self.is_previewing:
                self.is_previewing = False
                self.preview_button.config(text="▶️ Start Preview")
                self.preview_status.config(text="👁️ Preview: Off")

            self.line_draw_enabled = False
            self.draw_line_button.config(text="✏️ Draw Line", state='normal')

            self.video_title.config(text="🎥 AI Detection Active - Real-time Counting")
            self.capture_thread = threading.Thread(target=self.capture_loop, daemon=True)
            self.capture_thread.start()
        else:
            self.video_title.config(text="🎥 Detection Stopped")
            if self.capture_region:
                self.root.after(500, lambda: self.toggle_preview() if not self.is_previewing else None)

    def reset_count(self):
        """Reset all vehicle counts"""
        if messagebox.askyesno("🔄 Reset Counts", "Are you sure you want to reset all vehicle counts?"):
            self.vehicle_tracker.reset_counts()
            self.update_count_labels()
            print("✅ All directional counts reset.")

    def capture_screen(self):
        """Capture screen using PIL ImageGrab"""
        try:
            screenshot = ImageGrab.grab(bbox=self.capture_region)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            return frame
        except Exception as e:
            print(f"Screen capture error: {e}")
            return None

    def capture_loop(self):
        """Improved capture loop with better detection handling"""
        fps_counter = 0
        fps_start_time = time.time()
        
        print("🚀 Starting capture loop...")
        while self.is_capturing:
            try:
                frame = self.capture_screen()
                if frame is None:
                    time.sleep(0.1)
                    continue
                
                # YOLO detection
                results = self.model(frame, verbose=False, 
                                   conf=MODEL_CONFIG['confidence_threshold'], 
                                   iou=MODEL_CONFIG['iou_threshold'])
                
                # Process detections
                detections = []
                for r in results:
                    boxes = r.boxes
                    if boxes is not None:
                        for box in boxes:
                            cls = int(box.cls[0])
                            conf = float(box.conf[0])
                            if cls in VEHICLE_CLASSES and conf > MODEL_CONFIG['detection_confidence']:
                                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                                
                                width = x2 - x1
                                height = y2 - y1
                                if width > TRACKING_CONFIG['min_detection_size'] and height > TRACKING_CONFIG['min_detection_size']:
                                    detections.append({
                                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                                        'class': cls,
                                        'confidence': conf
                                    })
                
                # Update tracking
                self.vehicle_tracker.update_tracking(detections)
                
                # Draw visualizations dengan warna berbeda
                self.draw_detections_with_colors(frame)
                self.draw_counting_line(frame)
                
                # Check line crossings with direction
                if self.vehicle_tracker.check_line_crossings_directional(self.counting_line, self.line_settings):
                    self.update_count_labels()

                self.current_frame = frame.copy()
                self.root.after(0, self.update_display)
                
                # Calculate FPS
                fps_counter += 1
                if fps_counter % 5 == 0:
                    current_time = time.time()
                    fps = 5 / (current_time - fps_start_time)
                    fps_start_time = current_time
                    self.root.after(0, lambda f=fps: self.fps_label.config(text=f"📈 Detection FPS: {f:.1f}"))
                    self.root.after(0, lambda d=len(detections): self.detection_label.config(text=f"🎯 Detections: {d}"))
                
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                print(f"Capture error: {e}")
                time.sleep(0.1)

    def draw_detections_with_colors(self, frame):
        """Draw bounding boxes dengan warna berbeda berdasarkan status counted"""
        tracked_vehicles = self.vehicle_tracker.get_tracked_vehicles_with_status()
        
        for track_id, track in tracked_vehicles.items():
            x1, y1, x2, y2 = track['bbox']
            cls_name = CLASS_NAMES.get(track['class'], 'unknown')
            conf = track['confidence']
            is_counted = track.get('is_counted', False)
            
            # Pilih warna berdasarkan status
            if is_counted:
                box_color = COLOR_CONFIG['counted_vehicle']  # Abu-abu untuk yang sudah dihitung
                center_color = COLOR_CONFIG['center_dot_counted']
                path_color = COLOR_CONFIG['tracking_path_counted']
                label_prefix = "[COUNTED]"
            else:
                box_color = COLOR_CONFIG['active_vehicle']  # Hijau untuk yang aktif
                center_color = COLOR_CONFIG['center_dot_active']
                path_color = COLOR_CONFIG['tracking_path']
                label_prefix = "[ACTIVE]"
            
            # Draw rectangle
            cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
            
            # Draw label dengan status
            label = f"{label_prefix} {cls_name} {conf:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            
            # Background untuk label
            cv2.rectangle(frame, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), box_color, -1)
            
            # Text label
            cv2.putText(frame, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
            # Draw center dot
            center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
            cv2.circle(frame, (center_x, center_y), 3, center_color, -1)
            
            # Draw tracking path dengan warna yang sesuai
            path = track['path']
            if len(path) > 1:
                for i in range(1, len(path)):
                    cv2.line(frame, path[i-1], path[i], path_color, 2)

    def draw_counting_line(self, frame):
        """Draw the single counting line on the frame"""
        if self.counting_line:
            hex_color = self.line_settings['line_color'].lstrip('#')
            rgb_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            bgr_color = (rgb_color[2], rgb_color[1], rgb_color[0])
            thickness = self.line_settings['line_thickness']
            
            p1, p2 = self.counting_line
            cv2.line(frame, p1, p2, bgr_color, thickness)
            
            if self.line_settings['show_label']:
                label_text = self.line_settings['label_text']
                mid_x = (p1[0] + p2[0]) // 2
                mid_y = (p1[1] + p2[1]) // 2
                cv2.putText(frame, label_text, (mid_x + 10, mid_y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, bgr_color, 2)
                
                cv2.putText(frame, "UP", (p1[0] - 30, p1[1] - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                cv2.putText(frame, "DOWN", (p2[0] + 10, p2[1] + 20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    def start_line(self, event):
        """Start drawing the line on canvas"""
        if self.line_draw_enabled:
            self.drawing_line = True
            self.line_start_canvas = (event.x, event.y)
            self.canvas.delete("temp_line")

    def draw_line_preview(self, event):
        """Draw a temporary line as user drags"""
        if self.drawing_line and hasattr(self, 'line_start_canvas'):
            self.canvas.delete("temp_line")
            self.canvas.create_line(self.line_start_canvas[0], self.line_start_canvas[1], 
                                    event.x, event.y, 
                                    fill=self.line_settings['line_color'], 
                                    width=self.line_settings['line_thickness'], 
                                    tags="temp_line")

    def end_line(self, event):
        """End line drawing and set the single counting line"""
        if self.drawing_line and hasattr(self, 'line_start_canvas'):
            self.drawing_line = False
            self.canvas.delete("temp_line")

            p1_canvas = self.line_start_canvas
            p2_canvas = (event.x, event.y)

            # Convert canvas coordinates to frame coordinates
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            if self.current_frame is not None:
                frame_height, frame_width = self.current_frame.shape[:2]
            else:
                frame_width = self.capture_region[2] - self.capture_region[0] if self.capture_region else canvas_width
                frame_height = self.capture_region[3] - self.capture_region[1] if self.capture_region else canvas_height

            frame_aspect = frame_width / frame_height
            canvas_aspect = canvas_width / canvas_height

            if frame_aspect > canvas_aspect:
                scale = canvas_width / frame_width
                new_height = int(frame_height * scale)
                y_offset = (canvas_height - new_height) // 2
                x_offset = 0
            else:
                scale = canvas_height / frame_height
                new_width = int(frame_width * scale)
                x_offset = (canvas_width - new_width) // 2
                y_offset = 0

            def canvas_to_frame(x, y):
                x_adj = x - x_offset
                y_adj = y - y_offset
                x_frame = int(x_adj / scale)
                y_frame = int(y_adj / scale)
                x_frame = max(0, min(frame_width - 1, x_frame))
                y_frame = max(0, min(frame_height - 1, y_frame))
                return (x_frame, y_frame)

            p1 = canvas_to_frame(*p1_canvas)
            p2 = canvas_to_frame(*p2_canvas)

            if math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2) > 10:
                self.counting_line = [p1, p2]
                self.line_drawn = True
                self.line_draw_enabled = False
                self.draw_line_button.config(text="✏️ Draw Line", state='normal')
                self.line_status.config(text="📏 Line: 1 drawn")
                self.instructions.config(text="✅ Counting line ready! Start detection to count vehicles.")
            else:
                messagebox.showwarning("⚠️ Warning", "Line too short. Please draw a longer line.")
            
            del self.line_start_canvas

    def update_display(self):
        """Update the Tkinter canvas with the current frame"""
        if self.current_frame is not None:
            img = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)

            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            if canvas_width < 10 or canvas_height < 10:
                return

            img_width, img_height = img.size
            aspect_ratio = img_width / img_height
            canvas_aspect_ratio = canvas_width / canvas_height

            if aspect_ratio > canvas_aspect_ratio:
                new_width = canvas_width
                new_height = int(canvas_width / aspect_ratio)
            else:
                new_height = canvas_height
                new_width = int(canvas_height * aspect_ratio)

            img = img.resize((new_width, new_height), Image.LANCZOS)
            self.photo = ImageTk.PhotoImage(image=img)

            self.canvas.delete("all")
            self.canvas.create_image(canvas_width / 2, canvas_height / 2, image=self.photo, anchor=tk.CENTER)
        
        self.root.update_idletasks()

    # Database operation methods
    def save_counts_to_db(self):
        """Save counts to database with modern feedback"""
        try:
            counts = self.vehicle_tracker.get_counts()
            self.db_handler.save_counts(
                counts['up'], counts['down'], 
                counts['total_up'], counts['total_down'],
                self.root
            )
            # Update connection status
            self.connection_status.config(text="🟢 DB Saved", fg='#28a745')
            self.root.after(3000, lambda: self.connection_status.config(text="🔴 DB Disconnected", fg='#dc3545'))
        except Exception as e:
            messagebox.showerror("💾 Database Error", f"Failed to save to database: {e}")

    def view_reports(self):
        """Open reports viewer"""
        messagebox.showinfo("📊 Reports", "Reports viewer will be implemented in next update!")

    def export_data(self):
        """Export data to CSV/Excel"""
        messagebox.showinfo("📤 Export", "Data export feature will be implemented in next update!")

    def update_count_labels(self):
        """Update count labels with modern styling"""
        counts = self.vehicle_tracker.get_counts()
        
        self.root.after(0, lambda: self.total_up_label.config(text=f"📈 Total UP: {counts['total_up']}"))
        self.root.after(0, lambda: self.total_down_label.config(text=f"📉 Total DOWN: {counts['total_down']}"))
        
        # Update individual vehicle counts
        vehicles = ['car', 'motorcycle', 'bus', 'truck']
        for vehicle in vehicles:
            up_count = counts['up'].get(vehicle, 0)
            down_count = counts['down'].get(vehicle, 0)
            
            up_label = getattr(self, f'{vehicle}_up_label')
            down_label = getattr(self, f'{vehicle}_down_label')
            
            self.root.after(0, lambda ul=up_label, uc=up_count: ul.config(text=f"↑{uc}"))
            self.root.after(0, lambda dl=down_label, dc=down_count: dl.config(text=f"↓{dc}"))

    def on_closing(self):
        """Handle application closing with modern cleanup"""
        if self.is_capturing:
            self.is_capturing = False
            if self.capture_thread and self.capture_thread.is_alive():
                self.capture_thread.join(timeout=1)
                
        if self.is_previewing:
            self.is_previewing = False
            if self.preview_thread and self.preview_thread.is_alive():
                self.preview_thread.join(timeout=1)

        self.db_handler.close_connection()
        self.root.destroy()

if __name__ == "__main__":
    app = ModernScreenVehicleCounter()
    app.root.mainloop()