import mss
import numpy as np
import cv2
from typing import Tuple, Optional, Dict, Any

class ScreenCapture:
    """MSS-based screen capture class that mimics cv2.VideoCapture interface"""
    
    def __init__(self, monitor: int = 1, region: Optional[Tuple[int, int, int, int]] = None):
        """
        Initialize screen capture
        
        Args:
            monitor: Monitor number to capture (1 for primary, 0 for all monitors)
            region: Tuple of (x, y, width, height) for custom capture region
        """
        self.sct = mss.mss()
        self.monitor = monitor
        self.region = region
        self.is_opened = True
        
        # Get monitor information
        self.monitors = self.sct.monitors
        
        if region:
            # Custom region
            self.capture_area = {
                "top": region[1],
                "left": region[0], 
                "width": region[2],
                "height": region[3]
            }
        else:
            # Use specified monitor
            if monitor < len(self.monitors):
                self.capture_area = self.monitors[monitor]
            else:
                print(f"Monitor {monitor} not found, using primary monitor")
                self.capture_area = self.monitors[1]
                
        print(f"Screen capture initialized:")
        print(f"  Capture area: {self.capture_area}")
        print(f"  Available monitors: {len(self.monitors) - 1}")
    
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Capture a frame from screen
        
        Returns:
            Tuple of (success, frame) where frame is numpy array in BGR format
        """
        try:
            # Capture screen
            screenshot = self.sct.grab(self.capture_area)
            
            # Convert to numpy array
            frame = np.array(screenshot)
            
            # Convert from BGRA to BGR (remove alpha channel)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            
            return True, frame
            
        except Exception as e:
            print(f"Screen capture error: {e}")
            return False, None
    
    def isOpened(self) -> bool:
        """Check if screen capture is available"""
        return self.is_opened
    
    def release(self):
        """Release screen capture resources"""
        if hasattr(self, 'sct'):
            self.sct.close()
        self.is_opened = False
    
    def get(self, prop: int) -> float:
        """Get capture properties (for compatibility with cv2.VideoCapture)"""
        if prop == cv2.CAP_PROP_FRAME_WIDTH:
            return float(self.capture_area.get('width', 1920))
        elif prop == cv2.CAP_PROP_FRAME_HEIGHT:
            return float(self.capture_area.get('height', 1080))
        elif prop == cv2.CAP_PROP_FPS:
            return 30.0  # Default FPS for screen capture
        else:
            return 0.0
    
    def set(self, prop: int, value: float) -> bool:
        """Set capture properties (limited support)"""
        # Screen capture doesn't support setting most properties
        return False
    
    @staticmethod
    def list_monitors():
        """List available monitors"""
        with mss.mss() as sct:
            monitors = sct.monitors
            print("Available monitors:")
            for i, monitor in enumerate(monitors):
                if i == 0:
                    print(f"  {i}: All monitors combined - {monitor}")
                else:
                    print(f"  {i}: Monitor {i} - {monitor}")
        return monitors