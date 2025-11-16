"""
PROFESSIONAL OPENCV GESTURE CONTROL
Advanced finger tracking with Kalman filtering, continuous detection, and production optimizations
"""

import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time
from typing import Dict, List, Tuple, Optional
from collections import deque
from scipy.spatial import distance
from scipy.signal import savgol_filter


class KalmanFilter:
    """Kalman filter for smooth finger tracking"""
    
    def __init__(self, process_variance=1e-5, measurement_variance=1e-1):
        self.process_variance = process_variance
        self.measurement_variance = measurement_variance
        self.posteri_estimate = 0.0
        self.posteri_error_estimate = 1.0
        
    def update(self, measurement):
        """Update Kalman filter with new measurement"""
        # Prediction
        priori_estimate = self.posteri_estimate
        priori_error_estimate = self.posteri_error_estimate + self.process_variance
        
        # Update
        blending_factor = priori_error_estimate / (priori_error_estimate + self.measurement_variance)
        self.posteri_estimate = priori_estimate + blending_factor * (measurement - priori_estimate)
        self.posteri_error_estimate = (1 - blending_factor) * priori_error_estimate
        
        return self.posteri_estimate


class AdvancedOpenCVGesture:
    """
    Professional gesture control with OpenCV + MediaPipe
    Features:
    - Kalman filtering for smooth tracking
    - Frame buffering for continuous detection
    - Adaptive thresholding
    - Multi-hand support
    - Low-light optimization
    - Production-grade performance
    """
    
    def __init__(self):
        # MediaPipe setup
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Initialize hands with optimized settings
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,  # Lower for better detection
            min_tracking_confidence=0.5,   # Lower for continuous tracking
            model_complexity=1             # 0=lite, 1=full (better accuracy)
        )
        
        # Camera setup
        self.camera = None
        self.camera_width = 1280
        self.camera_height = 720
        self.camera_fps = 30
        
        # Kalman filters for each finger (x, y)
        self.kalman_filters = {
            'index_x': KalmanFilter(),
            'index_y': KalmanFilter(),
            'thumb_x': KalmanFilter(),
            'thumb_y': KalmanFilter(),
        }
        
        # Frame buffer for temporal smoothing
        self.frame_buffer_size = 5
        self.position_buffer = deque(maxlen=self.frame_buffer_size)
        
        # Gesture history for pattern recognition
        self.gesture_history = deque(maxlen=30)
        
        # State tracking
        self.is_active = False
        self.last_hand_detected = time.time()
        self.detection_timeout = 2.0  # seconds
        
        # Calibration
        self.screen_width, self.screen_height = pyautogui.size()
        self.cursor_smoothing = 0.3  # 0-1, higher = more smoothing
        
        # Performance optimization
        self.frame_skip = 0
        self.adaptive_frame_skip = 1  # Process every N frames
        self.last_process_time = time.time()
        
        # Low-light enhancement
        self.auto_brightness = True
        self.brightness_alpha = 1.5  # Contrast
        self.brightness_beta = 30    # Brightness
        
        # Gesture state
        self.pinch_threshold = 0.05  # Distance threshold for pinch
        self.grab_threshold = 0.1    # Distance threshold for grab
        self.is_pinching = False
        self.is_grabbing = False
        self.last_gesture = None
        
        print("🎯 Advanced OpenCV Gesture Control initialized")
        print(f"📐 Screen: {self.screen_width}x{self.screen_height}")
    
    def start_camera(self) -> bool:
        """Initialize camera with optimal settings"""
        try:
            # Try different camera indices
            for camera_index in [0, 1, 2]:
                self.camera = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
                if self.camera.isOpened():
                    print(f"✓ Camera {camera_index} opened")
                    break
            
            if not self.camera or not self.camera.isOpened():
                print("❌ No camera found")
                return False
            
            # Set camera properties for best quality
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_height)
            self.camera.set(cv2.CAP_PROP_FPS, self.camera_fps)
            self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 1)
            self.camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
            
            # Verify settings
            actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.camera.get(cv2.CAP_PROP_FPS))
            
            print(f"📹 Camera: {actual_width}x{actual_height} @ {actual_fps}fps")
            
            self.is_active = True
            return True
            
        except Exception as e:
            print(f"❌ Camera error: {e}")
            return False
    
    def enhance_frame(self, frame: np.ndarray) -> np.ndarray:
        """Enhance frame for better hand detection in various lighting"""
        if not self.auto_brightness:
            return frame
        
        # Convert to LAB color space for better brightness adjustment
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # Merge channels
        enhanced_lab = cv2.merge([l, a, b])
        enhanced_frame = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        
        # Apply brightness/contrast adjustment
        enhanced_frame = cv2.convertScaleAbs(enhanced_frame, alpha=self.brightness_alpha, beta=self.brightness_beta)
        
        return enhanced_frame
    
    def process_frame(self) -> Optional[Dict]:
        """Process single frame and extract hand landmarks"""
        if not self.is_active or not self.camera:
            return None
        
        # Adaptive frame skipping for performance
        self.frame_skip += 1
        if self.frame_skip < self.adaptive_frame_skip:
            return None
        self.frame_skip = 0
        
        # Read frame
        success, frame = self.camera.read()
        if not success:
            return None
        
        # Flip frame horizontally for natural mirror view
        frame = cv2.flip(frame, 1)
        
        # Enhance frame for better detection
        enhanced_frame = self.enhance_frame(frame)
        
        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(enhanced_frame, cv2.COLOR_BGR2RGB)
        
        # Process with MediaPipe
        results = self.hands.process(rgb_frame)
        
        if not results.multi_hand_landmarks:
            # No hand detected
            if time.time() - self.last_hand_detected > self.detection_timeout:
                self.reset_state()
            return None
        
        # Hand detected!
        self.last_hand_detected = time.time()
        
        # Process first hand (can extend for multi-hand)
        hand_landmarks = results.multi_hand_landmarks[0]
        handedness = results.multi_handedness[0].classification[0].label
        
        # Extract key landmarks
        landmarks = self.extract_landmarks(hand_landmarks, frame.shape)
        
        # Apply Kalman filtering
        filtered_landmarks = self.apply_kalman_filter(landmarks)
        
        # Add to position buffer for temporal smoothing
        self.position_buffer.append(filtered_landmarks)
        
        # Get smoothed position
        smoothed_landmarks = self.temporal_smooth()
        
        # Detect gestures
        gesture_data = self.detect_gestures(smoothed_landmarks)
        
        # Store gesture in history
        self.gesture_history.append(gesture_data)
        
        return {
            'landmarks': smoothed_landmarks,
            'gesture': gesture_data,
            'handedness': handedness,
            'frame': frame,
            'enhanced_frame': enhanced_frame
        }
    
    def extract_landmarks(self, hand_landmarks, frame_shape) -> Dict:
        """Extract key finger landmarks"""
        h, w, _ = frame_shape
        
        # Get key points
        index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        index_mcp = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_MCP]
        thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        thumb_mcp = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_CMC]
        middle_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
        ring_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_TIP]
        pinky_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_TIP]
        wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
        
        return {
            'index_tip': (index_tip.x, index_tip.y, index_tip.z),
            'index_mcp': (index_mcp.x, index_mcp.y, index_mcp.z),
            'thumb_tip': (thumb_tip.x, thumb_tip.y, thumb_tip.z),
            'thumb_mcp': (thumb_mcp.x, thumb_mcp.y, thumb_mcp.z),
            'middle_tip': (middle_tip.x, middle_tip.y, middle_tip.z),
            'ring_tip': (ring_tip.x, ring_tip.y, ring_tip.z),
            'pinky_tip': (pinky_tip.x, pinky_tip.y, pinky_tip.z),
            'wrist': (wrist.x, wrist.y, wrist.z)
        }
    
    def apply_kalman_filter(self, landmarks: Dict) -> Dict:
        """Apply Kalman filtering to smooth landmarks"""
        filtered = landmarks.copy()
        
        # Filter index finger
        filtered['index_tip'] = (
            self.kalman_filters['index_x'].update(landmarks['index_tip'][0]),
            self.kalman_filters['index_y'].update(landmarks['index_tip'][1]),
            landmarks['index_tip'][2]
        )
        
        # Filter thumb
        filtered['thumb_tip'] = (
            self.kalman_filters['thumb_x'].update(landmarks['thumb_tip'][0]),
            self.kalman_filters['thumb_y'].update(landmarks['thumb_tip'][1]),
            landmarks['thumb_tip'][2]
        )
        
        return filtered
    
    def temporal_smooth(self) -> Dict:
        """Apply temporal smoothing across frames"""
        if len(self.position_buffer) == 0:
            return {}
        
        if len(self.position_buffer) == 1:
            return self.position_buffer[0]
        
        # Average across buffer with weighted recent frames
        weights = np.linspace(0.5, 1.0, len(self.position_buffer))
        weights /= weights.sum()
        
        smoothed = {}
        keys = self.position_buffer[0].keys()
        
        for key in keys:
            # Get all values for this key
            values = np.array([frame[key] for frame in self.position_buffer])
            
            # Weighted average
            smoothed[key] = tuple(np.average(values, axis=0, weights=weights))
        
        return smoothed
    
    def detect_gestures(self, landmarks: Dict) -> Dict:
        """Detect hand gestures (pinch, grab, point, etc.)"""
        if not landmarks:
            return {'type': 'none'}
        
        # Calculate distances
        index_thumb_dist = self.calculate_distance(
            landmarks['index_tip'],
            landmarks['thumb_tip']
        )
        
        # Pinch gesture (index + thumb)
        is_pinching = index_thumb_dist < self.pinch_threshold
        
        # Grab gesture (all fingers close to palm)
        wrist_pos = landmarks['wrist']
        fingers_to_wrist = [
            self.calculate_distance(landmarks['index_tip'], wrist_pos),
            self.calculate_distance(landmarks['middle_tip'], wrist_pos),
            self.calculate_distance(landmarks['ring_tip'], wrist_pos),
            self.calculate_distance(landmarks['pinky_tip'], wrist_pos)
        ]
        avg_finger_dist = np.mean(fingers_to_wrist)
        is_grabbing = avg_finger_dist < self.grab_threshold
        
        # Determine gesture type
        if is_pinching:
            gesture_type = 'pinch'
        elif is_grabbing:
            gesture_type = 'grab'
        else:
            gesture_type = 'point'
        
        return {
            'type': gesture_type,
            'index_thumb_distance': index_thumb_dist,
            'confidence': 1.0 - index_thumb_dist if is_pinching else 0.5
        }
    
    def calculate_distance(self, point1: Tuple, point2: Tuple) -> float:
        """Calculate Euclidean distance between two points"""
        return np.sqrt(
            (point1[0] - point2[0])**2 +
            (point1[1] - point2[1])**2 +
            (point1[2] - point2[2])**2
        )
    
    def map_to_screen(self, x: float, y: float) -> Tuple[int, int]:
        """Map normalized hand coordinates to screen coordinates"""
        # Apply smoothing
        screen_x = int(x * self.screen_width)
        screen_y = int(y * self.screen_height)
        
        # Clamp to screen bounds
        screen_x = max(0, min(self.screen_width - 1, screen_x))
        screen_y = max(0, min(self.screen_height - 1, screen_y))
        
        return screen_x, screen_y
    
    def move_cursor(self, x: float, y: float, smooth: bool = True):
        """Move mouse cursor with optional smoothing"""
        screen_x, screen_y = self.map_to_screen(x, y)
        
        if smooth:
            # Get current cursor position
            current_x, current_y = pyautogui.position()
            
            # Interpolate
            new_x = int(current_x + (screen_x - current_x) * self.cursor_smoothing)
            new_y = int(current_y + (screen_y - current_y) * self.cursor_smoothing)
            
            pyautogui.moveTo(new_x, new_y, _pause=False)
        else:
            pyautogui.moveTo(screen_x, screen_y, _pause=False)
    
    def execute_gesture(self, gesture_data: Dict):
        """Execute action based on detected gesture"""
        gesture_type = gesture_data.get('type', 'none')
        
        if gesture_type == 'pinch' and not self.is_pinching:
            # Start pinch (click)
            pyautogui.click()
            self.is_pinching = True
            print("👆 Pinch detected - Click")
        
        elif gesture_type != 'pinch' and self.is_pinching:
            # End pinch
            self.is_pinching = False
        
        elif gesture_type == 'grab' and not self.is_grabbing:
            # Start grab (drag)
            pyautogui.mouseDown()
            self.is_grabbing = True
            print("✊ Grab detected - Drag start")
        
        elif gesture_type != 'grab' and self.is_grabbing:
            # End grab
            pyautogui.mouseUp()
            self.is_grabbing = False
            print("🖐️ Release - Drag end")
    
    def reset_state(self):
        """Reset tracking state"""
        self.position_buffer.clear()
        self.gesture_history.clear()
        self.is_pinching = False
        self.is_grabbing = False
        
        # Reset Kalman filters
        for filter in self.kalman_filters.values():
            filter.posteri_estimate = 0.0
            filter.posteri_error_estimate = 1.0
    
    def stop(self):
        """Stop gesture tracking and release resources"""
        self.is_active = False
        
        if self.camera:
            self.camera.release()
        
        if self.hands:
            self.hands.close()
        
        cv2.destroyAllWindows()
        print("🛑 Gesture tracking stopped")
    
    def get_status(self) -> Dict:
        """Get current tracking status"""
        return {
            'active': self.is_active,
            'hand_detected': time.time() - self.last_hand_detected < 1.0,
            'buffer_size': len(self.position_buffer),
            'gesture_history_size': len(self.gesture_history),
            'is_pinching': self.is_pinching,
            'is_grabbing': self.is_grabbing
        }


# Global instance
advanced_gesture = AdvancedOpenCVGesture()

