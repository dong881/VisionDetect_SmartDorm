"""
Hand gesture recognition capability using MediaPipe
Detects and recognizes hand gestures, specifically victory gesture
"""

from typing import Dict, Any, Optional
import numpy as np
import mediapipe as mp
from mediapipe.python.solutions import hands

from ..core.interfaces import Detector
from ..core.config import get_config
from ..utils.logger import get_logger


class HandGestureDetector(Detector):
    """Hand gesture detection using MediaPipe Hands"""
    
    # Gesture state constants
    GESTURE_NONE = 0
    GESTURE_POSSIBLE = 1
    GESTURE_CONFIRMED = 2
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize hand gesture detector
        
        Args:
            config: Configuration object (uses global if None)
        """
        self.config = config or get_config()
        self.logger = get_logger()
        self.mp_hands = None
        self._initialized = False
        
        # Gesture tracking state
        self.gesture_state = self.GESTURE_NONE
        self.gesture_start_time = 0
        self.gesture_confidence = 0
    
    def initialize(self) -> bool:
        """Initialize MediaPipe Hands model"""
        try:
            max_hands = self.config.get('hand_detection.max_num_hands', 1)
            min_detection = self.config.get('hand_detection.min_detection_confidence', 0.75)
            min_tracking = self.config.get('hand_detection.min_tracking_confidence', 0.6)
            static_mode = self.config.get('hand_detection.static_image_mode', False)
            
            self.mp_hands = hands.Hands(
                max_num_hands=max_hands,
                min_detection_confidence=min_detection,
                min_tracking_confidence=min_tracking,
                static_image_mode=static_mode
            )
            
            self._initialized = True
            self.logger.info(f"Hand gesture detector initialized (confidence: {min_detection})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize hand gesture detector: {e}")
            return False
    
    def cleanup(self):
        """Clean up resources"""
        if self.mp_hands:
            self.mp_hands.close()
            self.mp_hands = None
        self._initialized = False
        self.logger.info("Hand gesture detector cleaned up")
    
    def is_ready(self) -> bool:
        """Check if detector is ready"""
        return self._initialized and self.mp_hands is not None
    
    def detect(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Detect hand gestures in frame
        
        Args:
            frame: BGR image frame
            
        Returns:
            Dictionary with detection results:
            {
                'hand_landmarks': hand landmarks or None,
                'gesture_type': detected gesture type,
                'gesture_confidence': confidence score (0-1),
                'gesture_state': current gesture state
            }
        """
        if not self.is_ready():
            return {
                'hand_landmarks': None,
                'gesture_type': None,
                'gesture_confidence': 0.0,
                'gesture_state': self.GESTURE_NONE
            }
        
        try:
            # Convert BGR to RGB
            frame_rgb = frame[:, :, ::-1]
            
            # Process frame
            results = self.mp_hands.process(frame_rgb)
            
            # Detect gestures
            gesture_type = None
            gesture_confidence = 0.0
            
            if results.multi_hand_landmarks:
                gesture_confidence = self._is_victory_gesture(
                    results.multi_hand_landmarks[0]
                )
                if gesture_confidence > 0.5:
                    gesture_type = "victory"
            
            return {
                'hand_landmarks': results.multi_hand_landmarks,
                'gesture_type': gesture_type,
                'gesture_confidence': gesture_confidence,
                'gesture_state': self.gesture_state
            }
            
        except Exception as e:
            self.logger.error(f"Error in hand gesture detection: {e}")
            return {
                'hand_landmarks': None,
                'gesture_type': None,
                'gesture_confidence': 0.0,
                'gesture_state': self.GESTURE_NONE
            }
    
    def _calculate_finger_angles(self, hand_landmarks):
        """
        Calculate finger bend angles
        
        Args:
            hand_landmarks: MediaPipe hand landmarks
            
        Returns:
            List of bend angles for each finger (radians)
        """
        # Finger joint indices
        finger_bases = [1, 5, 9, 13, 17]
        finger_pips = [2, 6, 10, 14, 18]
        finger_dips = [3, 7, 11, 15, 19]
        finger_tips = [4, 8, 12, 16, 20]
        
        angles = []
        
        for f in range(5):  # For each finger
            base = hand_landmarks.landmark[finger_bases[f]]
            pip = hand_landmarks.landmark[finger_pips[f]]
            dip = hand_landmarks.landmark[finger_dips[f]]
            tip = hand_landmarks.landmark[finger_tips[f]]
            
            # Calculate vectors
            v1 = np.array([pip.x - base.x, pip.y - base.y, pip.z - base.z])
            v2 = np.array([dip.x - pip.x, dip.y - pip.y, dip.z - pip.z])
            v3 = np.array([tip.x - dip.x, tip.y - dip.y, tip.z - dip.z])
            
            # Normalize vectors
            v1 = v1 / (np.linalg.norm(v1) + 1e-6)
            v2 = v2 / (np.linalg.norm(v2) + 1e-6)
            v3 = v3 / (np.linalg.norm(v3) + 1e-6)
            
            # Calculate joint angles
            angle1 = np.arccos(np.clip(np.dot(v1, v2), -1.0, 1.0))
            angle2 = np.arccos(np.clip(np.dot(v2, v3), -1.0, 1.0))
            
            total_bend = angle1 + angle2
            angles.append(total_bend)
        
        return angles
    
    def _is_victory_gesture(self, hand_landmarks) -> float:
        """
        Detect victory gesture (V sign)
        
        Args:
            hand_landmarks: MediaPipe hand landmarks
            
        Returns:
            Confidence score (0-1)
        """
        if not hand_landmarks:
            return 0.0
        
        try:
            # Calculate finger angles
            angles = self._calculate_finger_angles(hand_landmarks)
            
            # Get key landmarks
            index_tip = hand_landmarks.landmark[8]
            index_dip = hand_landmarks.landmark[7]
            index_mcp = hand_landmarks.landmark[5]
            
            middle_tip = hand_landmarks.landmark[12]
            middle_dip = hand_landmarks.landmark[11]
            middle_mcp = hand_landmarks.landmark[9]
            
            ring_tip = hand_landmarks.landmark[16]
            ring_mcp = hand_landmarks.landmark[13]
            
            pinky_tip = hand_landmarks.landmark[20]
            pinky_mcp = hand_landmarks.landmark[17]
            
            thumb_tip = hand_landmarks.landmark[4]
            
            # Check if index and middle fingers are straight
            index_straight = (angles[1] < 0.7) and (index_tip.z < index_dip.z)
            middle_straight = (angles[2] < 0.7) and (middle_tip.z < middle_dip.z)
            
            # Check if other fingers are bent
            ring_bent = (angles[3] > 1.0) and (ring_tip.y > ring_mcp.y)
            pinky_bent = (angles[4] > 1.0) and (pinky_tip.y > pinky_mcp.y)
            
            # Check thumb position
            thumb_away = (
                (thumb_tip.x < index_mcp.x) or 
                (thumb_tip.x > middle_mcp.x)
            )
            
            # Calculate angle between index and middle fingers
            v_index = np.array([
                index_tip.x - index_mcp.x,
                index_tip.y - index_mcp.y
            ])
            v_middle = np.array([
                middle_tip.x - middle_mcp.x,
                middle_tip.y - middle_mcp.y
            ])
            
            # Normalize and calculate angle
            v_index = v_index / (np.linalg.norm(v_index) + 1e-6)
            v_middle = v_middle / (np.linalg.norm(v_middle) + 1e-6)
            
            angle_between = np.arccos(np.clip(np.dot(v_index, v_middle), -1.0, 1.0))
            angle_deg = np.degrees(angle_between)
            
            # V gesture should have angle between 20-60 degrees
            good_angle = 20 < angle_deg < 60
            
            # Check if fingers are at similar height
            similar_height = abs(index_tip.y - middle_tip.y) < 0.1
            
            # Calculate confidence
            confidence = 0.0
            if index_straight:
                confidence += 0.2
            if middle_straight:
                confidence += 0.2
            if ring_bent and pinky_bent:
                confidence += 0.2
            if good_angle:
                confidence += 0.2
            if similar_height and thumb_away:
                confidence += 0.2
            
            return confidence
            
        except Exception as e:
            self.logger.error(f"Error calculating victory gesture: {e}")
            return 0.0
    
    def update_gesture_state(self, gesture_confidence: float, current_time: float) -> bool:
        """
        Update gesture state machine
        
        Args:
            gesture_confidence: Current gesture confidence
            current_time: Current timestamp
            
        Returns:
            True if gesture is confirmed
        """
        hold_time = self.config.get('gesture.hold_time', 1.5)
        threshold = self.config.get('gesture.victory_confidence_threshold', 0.8)
        
        if gesture_confidence > threshold:
            if self.gesture_state == self.GESTURE_NONE:
                self.gesture_state = self.GESTURE_POSSIBLE
                self.gesture_start_time = current_time
                self.gesture_confidence = gesture_confidence
                self.logger.debug(f"Possible gesture detected: {gesture_confidence:.2f}")
            
            elif self.gesture_state == self.GESTURE_POSSIBLE:
                self.gesture_confidence = max(self.gesture_confidence, gesture_confidence)
                
                if current_time - self.gesture_start_time >= hold_time:
                    self.gesture_state = self.GESTURE_CONFIRMED
                    self.logger.info(f"Gesture confirmed: {self.gesture_confidence:.2f}")
                    return True
        
        elif gesture_confidence > 0.5:
            if self.gesture_state == self.GESTURE_POSSIBLE:
                # Smooth update
                self.gesture_confidence = 0.7 * self.gesture_confidence + 0.3 * gesture_confidence
        
        else:
            if self.gesture_state != self.GESTURE_NONE:
                self.logger.debug("Gesture tracking lost")
                self.gesture_state = self.GESTURE_NONE
                self.gesture_confidence = 0
        
        return False
    
    def reset_gesture_state(self):
        """Reset gesture tracking state"""
        self.gesture_state = self.GESTURE_NONE
        self.gesture_start_time = 0
        self.gesture_confidence = 0
