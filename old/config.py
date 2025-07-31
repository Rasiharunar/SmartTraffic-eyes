import argparse
from typing import Tuple, Optional

class Config:
    """Configuration management for vehicle detection system"""
    
    def __init__(self):
        self.input_type = "video"
        self.video_file = "1.mp4"
        self.screen_region = None
        self.monitor = 1
        self.fullscreen = False
        self.webcam_id = 0
        self.output_video = None
        self.show_output = True
        self.confidence_threshold = 0.5
        self.fps_limit = 30
        
    @classmethod
    def from_args(cls):
        """Create configuration from command line arguments"""
        parser = argparse.ArgumentParser(description='Vehicle Detection and Tracking')
        
        # Input source options
        parser.add_argument('--input', choices=['video', 'webcam', 'screen'], 
                          default='video', help='Input source type')
        parser.add_argument('--file', type=str, default='1.mp4', 
                          help='Video file path (for video input)')
        parser.add_argument('--webcam', type=int, default=0, 
                          help='Webcam device ID (for webcam input)')
        
        # Screen capture options
        parser.add_argument('--monitor', type=int, default=1, 
                          help='Monitor number for screen capture (1=primary)')
        parser.add_argument('--region', type=str, 
                          help='Screen capture region as "x,y,width,height"')
        parser.add_argument('--fullscreen', action='store_true', 
                          help='Capture full screen')
        parser.add_argument('--list-monitors', action='store_true',
                          help='List available monitors and exit')
        
        # Processing options
        parser.add_argument('--confidence', type=float, default=0.5,
                          help='Confidence threshold for detection')
        parser.add_argument('--fps', type=int, default=30,
                          help='Target FPS for processing')
        parser.add_argument('--output', type=str,
                          help='Output video file path')
        parser.add_argument('--no-display', action='store_true',
                          help='Disable display output')
        
        args = parser.parse_args()
        
        config = cls()
        config.input_type = args.input
        config.video_file = args.file
        config.webcam_id = args.webcam
        config.monitor = args.monitor
        config.fullscreen = args.fullscreen
        config.output_video = args.output
        config.show_output = not args.no_display
        config.confidence_threshold = args.confidence
        config.fps_limit = args.fps
        
        # Parse screen region
        if args.region:
            try:
                x, y, w, h = map(int, args.region.split(','))
                config.screen_region = (x, y, w, h)
            except ValueError:
                print("Invalid region format. Use: x,y,width,height")
                exit(1)
        
        return config, args.list_monitors
    
    def get_input_source(self):
        """Get the appropriate input source based on configuration"""
        if self.input_type == "video":
            import cv2
            return cv2.VideoCapture(self.video_file)
        
        elif self.input_type == "webcam":
            import cv2
            return cv2.VideoCapture(self.webcam_id)
        
        elif self.input_type == "screen":
            from screen_capture import ScreenCapture
            if self.fullscreen:
                return ScreenCapture(monitor=0)  # All monitors
            else:
                return ScreenCapture(monitor=self.monitor, region=self.screen_region)
        
        else:
            raise ValueError(f"Unknown input type: {self.input_type}")
    
    def print_config(self):
        """Print current configuration"""
        print("Configuration:")
        print(f"  Input type: {self.input_type}")
        if self.input_type == "video":
            print(f"  Video file: {self.video_file}")
        elif self.input_type == "webcam":
            print(f"  Webcam ID: {self.webcam_id}")
        elif self.input_type == "screen":
            print(f"  Monitor: {self.monitor}")
            print(f"  Region: {self.screen_region}")
            print(f"  Fullscreen: {self.fullscreen}")
        print(f"  Confidence threshold: {self.confidence_threshold}")
        print(f"  Target FPS: {self.fps_limit}")
        print(f"  Show output: {self.show_output}")
        print(f"  Output file: {self.output_video}")