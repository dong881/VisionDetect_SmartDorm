"""
Human pose detection capability using MediaPipe
Detects human presence and body landmarks
"""

from typing import Dict, Any, Optional
import numpy as np
import mediapipe as mp
from mediapipe.python.solutions import pose

from ..core.interfaces import Detector
from ..core.config import get_config
from ..utils.logger import get_logger


class PoseDetector(Detector):
    """Human pose detection using MediaPipe Pose"""
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize pose detector
        
        Args:
            config: Configuration object (uses global if None)
        """
        self.config = config or get_config()
        self.logger = get_logger()
        self.mp_pose = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize MediaPipe Pose model"""
        try:
            min_detection = self.config.get('pose_detection.min_detection_confidence', 0.6)
            min_tracking = self.config.get('pose_detection.min_tracking_confidence', 0.6)
            enable_seg = self.config.get('pose_detection.enable_segmentation', True)
            static_mode = self.config.get('pose_detection.static_image_mode', False)
            
            self.mp_pose = pose.Pose(
                min_detection_confidence=min_detection,
                min_tracking_confidence=min_tracking,
                enable_segmentation=enable_seg,
                static_image_mode=static_mode
            )
            
            self._initialized = True
            self.logger.info(f"Pose detector initialized (confidence: {min_detection})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize pose detector: {e}")
            return False
    
    def cleanup(self):
        """Clean up resources"""
        if self.mp_pose:
            self.mp_pose.close()
            self.mp_pose = None
        self._initialized = False
        self.logger.info("Pose detector cleaned up")
    
    def is_ready(self) -> bool:
        """Check if detector is ready"""
        return self._initialized and self.mp_pose is not None
    
    def detect(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Detect human pose in frame
        
        Args:
            frame: BGR image frame
            
        Returns:
            Dictionary with detection results:
            {
                'pose_landmarks': pose landmarks object or None,
                'segmentation_mask': segmentation mask or None,
                'confidence': confidence score (0-1),
                'present': whether person is present (bool)
            }
        """
        if not self.is_ready():
            return {
                'pose_landmarks': None,
                'segmentation_mask': None,
                'confidence': 0.0,
                'present': False
            }
        
        try:
            # Convert BGR to RGB
            frame_rgb = frame[:, :, ::-1]  # Faster than cv2.cvtColor
            
            # Process frame
            results = self.mp_pose.process(frame_rgb)
            
            # Calculate confidence
            confidence = self._calculate_confidence(results)
            
            return {
                'pose_landmarks': results.pose_landmarks,
                'segmentation_mask': results.segmentation_mask,
                'confidence': confidence,
                'present': confidence > 0.5
            }
            
        except Exception as e:
            self.logger.error(f"Error in pose detection: {e}")
            return {
                'pose_landmarks': None,
                'segmentation_mask': None,
                'confidence': 0.0,
                'present': False
            }
    
    def _calculate_confidence(self, pose_results) -> float:
        """
        Calculate confidence score for person presence
        
        Args:
            pose_results: MediaPipe pose detection results
            
        Returns:
            Confidence score (0-1)
        """
        if not pose_results.pose_landmarks:
            return 0.0
        
        landmarks = pose_results.pose_landmarks.landmark
        
        # Count valid landmarks with high visibility
        valid_landmarks = sum(1 for lm in landmarks if lm.visibility > 0.7)
        landmark_confidence = valid_landmarks / len(landmarks)
        
        # Check key body parts visibility
        nose = landmarks[pose.PoseLandmark.NOSE]
        left_shoulder = landmarks[pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[pose.PoseLandmark.RIGHT_SHOULDER]
        
        # Upper body visible check
        upper_body_visible = (
            left_shoulder.visibility > 0.7 and 
            right_shoulder.visibility > 0.7
        )
        
        # Check if person is in center region
        key_points = [nose, left_shoulder, right_shoulder]
        avg_x = sum(pt.x for pt in key_points if pt.visibility > 0.5) / len(key_points)
        in_center = 0.3 < avg_x < 0.7
        
        # Check distance (shoulder width indicates proximity)
        shoulder_distance = (
            (left_shoulder.x - right_shoulder.x)**2 + 
            (left_shoulder.y - right_shoulder.y)**2
        )**0.5
        is_close = shoulder_distance > 0.2
        
        # Segmentation score
        segmentation_score = 0.0
        if pose_results.segmentation_mask is not None:
            seg_threshold = self.config.get('presence.segmentation_threshold', 0.5)
            mask = pose_results.segmentation_mask
            total_pixels = mask.shape[0] * mask.shape[1]
            human_pixels = np.sum(mask > seg_threshold)
            segmentation_score = min(human_pixels / total_pixels / 0.3, 1.0)
        
        # Weighted combination
        position_score = (0.4 if in_center else 0.0) + (0.3 if is_close else 0.0)
        visibility_score = 0.3 if upper_body_visible else 0.0
        
        final_confidence = (
            0.4 * landmark_confidence + 
            0.3 * position_score + 
            0.2 * visibility_score + 
            0.1 * segmentation_score
        )
        
        return min(final_confidence, 1.0)
