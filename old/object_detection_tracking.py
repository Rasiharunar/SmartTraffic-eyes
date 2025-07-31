import cv2
import numpy as np
import time
from config import Config
from screen_capture import ScreenCapture

def main():
    """Main function for vehicle detection and tracking"""
    
    # Parse configuration
    config, list_monitors = Config.from_args()
    
    # List monitors if requested
    if list_monitors:
        ScreenCapture.list_monitors()
        return
    
    # Print configuration
    config.print_config()
    
    # Initialize input source
    try:
        cap = config.get_input_source()
        if not cap.isOpened():
            print(f"Error: Cannot open {config.input_type} source")
            return
    except Exception as e:
        print(f"Error initializing input source: {e}")
        return
    
    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"Input resolution: {width}x{height}")
    print(f"Input FPS: {fps}")
    
    # Initialize video writer if output is specified
    out = None
    if config.output_video:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(config.output_video, fourcc, config.fps_limit, (width, height))
    
    # Performance tracking
    frame_count = 0
    start_time = time.time()
    fps_counter = 0
    fps_display = 0
    
    # Frame rate control
    target_frame_time = 1.0 / config.fps_limit if config.fps_limit > 0 else 0
    
    print(f"\nStarting vehicle detection...")
    print(f"Press 'q' to quit, 's' to save screenshot")
    
    try:
        while True:
            frame_start = time.time()
            
            # Read frame
            ret, frame = cap.read()
            if not ret:
                if config.input_type == "video":
                    print("End of video file reached")
                    break
                else:
                    print("Failed to capture frame")
                    continue
            
            frame_count += 1
            fps_counter += 1
            
            # TODO: Add your existing YOLOv8 + DeepSORT processing here
            # For now, just display the frame with some info
            
            # Add info overlay
            info_text = f"Input: {config.input_type.upper()}"
            cv2.putText(frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                       1, (0, 255, 0), 2)
            
            fps_text = f"FPS: {fps_display:.1f}"
            cv2.putText(frame, fps_text, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 
                       1, (0, 255, 0), 2)
            
            frame_text = f"Frame: {frame_count}"
            cv2.putText(frame, frame_text, (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 
                       1, (0, 255, 0), 2)
            
            # Calculate and display FPS
            if fps_counter >= 30:  # Update FPS display every 30 frames
                current_time = time.time()
                fps_display = fps_counter / (current_time - start_time)
                fps_counter = 0
                start_time = current_time
            
            # Save frame to output video
            if out is not None:
                out.write(frame)
            
            # Display frame
            if config.show_output:
                cv2.imshow('Vehicle Detection - Press q to quit', frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    # Save screenshot
                    screenshot_name = f"screenshot_{int(time.time())}.jpg"
                    cv2.imwrite(screenshot_name, frame)
                    print(f"Screenshot saved: {screenshot_name}")
            
            # Frame rate control
            if target_frame_time > 0:
                frame_time = time.time() - frame_start
                if frame_time < target_frame_time:
                    time.sleep(target_frame_time - frame_time)
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    
    finally:
        # Cleanup
        print(f"\nProcessed {frame_count} frames")
        cap.release()
        if out is not None:
            out.release()
        cv2.destroyAllWindows()
        print("Cleanup completed")

if __name__ == "__main__":
    main()