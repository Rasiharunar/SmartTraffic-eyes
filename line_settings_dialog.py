"""
Dialog untuk pengaturan garis counting
"""

import tkinter as tk
from tkinter import ttk, colorchooser
from config import DEFAULT_LINE_SETTINGS

class LineSettingsDialog:
    def __init__(self, parent, current_settings=None):
        self.parent = parent
        self.result = None
        self.settings = DEFAULT_LINE_SETTINGS.copy()
        
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
        
        self._create_line_type_section(main_frame)
        self._create_appearance_section(main_frame)
        self._create_label_section(main_frame)
        self._create_detection_section(main_frame)
        self._create_preset_section(main_frame)
        self._create_button_section(main_frame)
        
    def _create_line_type_section(self, parent):
        """Create line type selection section"""
        type_frame = ttk.LabelFrame(parent, text="Line Type", padding=10)
        type_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.line_type_var = tk.StringVar(value=self.settings['line_type'])
        ttk.Radiobutton(type_frame, text="Manual Draw", variable=self.line_type_var, 
                        value="manual").pack(anchor=tk.W)
        ttk.Radiobutton(type_frame, text="Horizontal Line", variable=self.line_type_var, 
                        value="horizontal").pack(anchor=tk.W)
        ttk.Radiobutton(type_frame, text="Vertical Line", variable=self.line_type_var, 
                        value="vertical").pack(anchor=tk.W)
    
    def _create_appearance_section(self, parent):
        """Create appearance settings section"""
        appearance_frame = ttk.LabelFrame(parent, text="Appearance", padding=10)
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
    
    def _create_label_section(self, parent):
        """Create label settings section"""
        label_frame = ttk.LabelFrame(parent, text="Label", padding=10)
        label_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.show_label_var = tk.BooleanVar(value=self.settings['show_label'])
        ttk.Checkbutton(label_frame, text="Show Label", 
                        variable=self.show_label_var).pack(anchor=tk.W)
        
        text_frame = ttk.Frame(label_frame)
        text_frame.pack(fill=tk.X, pady=5)
        ttk.Label(text_frame, text="Text:").pack(side=tk.LEFT)
        
        self.label_text_var = tk.StringVar(value=self.settings['label_text'])
        ttk.Entry(text_frame, textvariable=self.label_text_var).pack(
            side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
    
    def _create_detection_section(self, parent):
        """Create detection settings section"""
        detection_frame = ttk.LabelFrame(parent, text="Detection", padding=10)
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
    
    def _create_preset_section(self, parent):
        """Create preset buttons section"""
        preset_frame = ttk.LabelFrame(parent, text="Presets", padding=10)
        preset_frame.pack(fill=tk.X, pady=(0, 10))
        
        preset_buttons_frame = ttk.Frame(preset_frame)
        preset_buttons_frame.pack()
        
        ttk.Button(preset_buttons_frame, text="Red Line", 
                   command=lambda: self.apply_preset('red')).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_buttons_frame, text="Blue Line", 
                   command=lambda: self.apply_preset('blue')).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_buttons_frame, text="Green Line", 
                   command=lambda: self.apply_preset('green')).pack(side=tk.LEFT, padx=2)
    
    def _create_button_section(self, parent):
        """Create dialog buttons section"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Reset", command=self.reset_clicked).pack(side=tk.LEFT)
        
    def choose_color(self):
        color = colorchooser.askcolor(initialcolor=self.color_var.get())
        if color[1]:
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
        self.color_var.set(DEFAULT_LINE_SETTINGS['line_color'])
        self.color_button.config(bg=DEFAULT_LINE_SETTINGS['line_color'])
        self.thickness_var.set(DEFAULT_LINE_SETTINGS['line_thickness'])
        self.style_var.set(DEFAULT_LINE_SETTINGS['line_style'])
        self.show_label_var.set(DEFAULT_LINE_SETTINGS['show_label'])
        self.label_text_var.set(DEFAULT_LINE_SETTINGS['label_text'])
        self.threshold_var.set(DEFAULT_LINE_SETTINGS['detection_threshold'])
        self.line_type_var.set(DEFAULT_LINE_SETTINGS['line_type'])
        
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