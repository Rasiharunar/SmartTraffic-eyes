"""
Vehicle tracking dan line crossing detection
"""

import numpy as np
import math
import time
from collections import defaultdict
from config import TRACKING_CONFIG, CLASS_NAMES

class VehicleTracker:
    def __init__(self):
        self.tracked_vehicles = {}
        self.next_id = 0
        self.counted_ids = set()
        
        # Directional counting
        self.vehicle_count_up = defaultdict(int)
        self.vehicle_count_down = defaultdict(int)
        self.total_count_up = 0
        self.total_count_down = 0
        
    def update_tracking(self, detections):
        """Update vehicle tracking with improved algorithm"""
        max_distance = TRACKING_CONFIG['max_distance']
        updated_tracks = {}
        
        for detection in detections:
            bbox = detection['bbox']
            center = [(bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2]
            
            best_match = None
            best_distance = max_distance
            
            for track_id, track in self.tracked_vehicles.items():
                if track['class'] == detection['class']:
                    # Calculate distance
                    distance = math.sqrt(
                        (center[0] - track['center'][0])**2 + 
                        (center[1] - track['center'][1])**2
                    )
                    
                    # Add velocity prediction for better tracking
                    if len(track['path']) >= 2:
                        last_movement = [
                            track['path'][-1][0] - track['path'][-2][0],
                            track['path'][-1][1] - track['path'][-2][1]
                        ]
                        predicted_pos = [
                            track['center'][0] + last_movement[0],
                            track['center'][1] + last_movement[1]
                        ]
                        predicted_distance = math.sqrt(
                            (center[0] - predicted_pos[0])**2 + 
                            (center[1] - predicted_pos[1])**2
                        )
                        distance = min(distance, predicted_distance)
                    
                    if distance < best_distance:
                        best_distance = distance
                        best_match = track_id
            
            if best_match is not None:
                path_history = self.tracked_vehicles[best_match]['path']
                if len(path_history) > TRACKING_CONFIG['path_history_length']:
                    path_history = path_history[-TRACKING_CONFIG['path_history_length']:]
                    
                updated_tracks[best_match] = {
                    'center': center,
                    'bbox': bbox,
                    'class': detection['class'],
                    'last_seen': time.time(),
                    'path': path_history + [center],
                    'confidence': detection['confidence'],
                    'is_counted': best_match in self.counted_ids  # Add counted status
                }
            else:
                updated_tracks[self.next_id] = {
                    'center': center,
                    'bbox': bbox,
                    'class': detection['class'],
                    'last_seen': time.time(),
                    'path': [center],
                    'confidence': detection['confidence'],
                    'is_counted': False  # New vehicles are not counted yet
                }
                self.next_id += 1
                
        # Remove old tracks
        current_time = time.time()
        self.tracked_vehicles = {
            tid: track for tid, track in updated_tracks.items() 
            if current_time - track['last_seen'] < TRACKING_CONFIG['track_timeout']
        }

    def check_line_crossings_directional(self, counting_line, line_settings):
        """Check for line crossings with direction detection"""
        if not counting_line:
            return False
            
        threshold = line_settings['detection_threshold']
        line_p1 = np.array(counting_line[0])
        line_p2 = np.array(counting_line[1])
        count_updated = False
        
        for track_id, track in list(self.tracked_vehicles.items()):
            if track_id in self.counted_ids:
                continue
                
            if len(track['path']) < 3:
                continue
                
            # Check multiple recent positions for more robust detection
            for i in range(len(track['path']) - 1, max(0, len(track['path']) - 3), -1):
                if i == 0:
                    break
                
                current_pos = np.array(track['path'][i])
                prev_pos = np.array(track['path'][i-1])
                
                # Calculate cross products to detect line crossing
                vec_p1_current = current_pos - line_p1
                vec_p1_prev = prev_pos - line_p1
                vec_line = line_p2 - line_p1
                
                cross_product_current = np.cross(vec_line, vec_p1_current)
                cross_product_prev = np.cross(vec_line, vec_p1_prev)
                
                # Check if vehicle crossed the line
                if cross_product_current * cross_product_prev < 0:
                    # Calculate distance to line
                    line_len_sq = np.sum((line_p2 - line_p1)**2)
                    if line_len_sq == 0:
                        dist_to_line = np.linalg.norm(current_pos - line_p1)
                    else:
                        t = max(0, min(1, np.dot(current_pos - line_p1, line_p2 - line_p1) / line_len_sq))
                        projection = line_p1 + t * (line_p2 - line_p1)
                        dist_to_line = np.linalg.norm(current_pos - projection)
                    
                    if dist_to_line < threshold:
                        vehicle_type = CLASS_NAMES.get(track['class'], 'unknown')
                        
                        if cross_product_current > 0:
                            direction = "UP"
                            self.vehicle_count_up[vehicle_type] += 1
                            self.total_count_up += 1
                        else:
                            direction = "DOWN"
                            self.vehicle_count_down[vehicle_type] += 1
                            self.total_count_down += 1
                        
                        self.counted_ids.add(track_id)
                        # Mark this track as counted
                        if track_id in self.tracked_vehicles:
                            self.tracked_vehicles[track_id]['is_counted'] = True
                        
                        print(f"Vehicle {track_id} ({vehicle_type}) *COUNTED* going {direction}!")
                        count_updated = True
                        break
        
        return count_updated

    def get_tracked_vehicles_with_status(self):
        """Get tracked vehicles with their counted status"""
        return self.tracked_vehicles

    def reset_counts(self):
        """Reset all vehicle counts"""
        self.vehicle_count_up = defaultdict(int)
        self.vehicle_count_down = defaultdict(int)
        self.total_count_up = 0
        self.total_count_down = 0
        self.counted_ids = set()
        self.tracked_vehicles = {}
        self.next_id = 0

    def get_counts(self):
        """Get current counts"""
        return {
            'up': dict(self.vehicle_count_up),
            'down': dict(self.vehicle_count_down),
            'total_up': self.total_count_up,
            'total_down': self.total_count_down
        }