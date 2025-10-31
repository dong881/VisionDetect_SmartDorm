"""
Camera capture capability
Handles video capture and frame management
"""

from typing import Optional, Tuple
import cv2
import numpy as np
import time
from threading import Thread, Lock

from ..core.interfaces import Capability
from ..core.config import get_config
from ..utils.logger import get_logger


class CameraCapture(Capability):
    """Video camera capture with threaded frame reading"""
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize camera capture
        
        Args:
            config: Configuration object (uses global if None)
        """
        self.config = config or get_config()
        self.logger = get_logger()
        
        self.cap = None
        self.frame = None
        self.frame_lock = Lock()
        self.capture_thread = None
        self.running = False
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize camera"""
        try:
            device_id = self.config.get('camera.device_id', 0)
            width = self.config.get('camera.width', 640)
            height = self.config.get('camera.height', 480)
            fps = self.config.get('camera.fps', 30)
            
            self.cap = cv2.VideoCapture(device_id)
            
            if not self.cap.isOpened():
                self.logger.error(f"Failed to open camera {device_id}")
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.cap.set(cv2.CAP_PROP_FPS, fps)
            
            # Verify settings
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            
            self.logger.info(
                f"Camera initialized: {actual_width}x{actual_height} @ {actual_fps}fps"
            )
            
            self._initialized = True
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize camera: {e}")
            return False
    
    def cleanup(self):
        """Clean up camera resources"""
        self.stop_capture()
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        self._initialized = False
        self.logger.info("Camera cleaned up")
    
    def is_ready(self) -> bool:
        """Check if camera is ready"""
        return self._initialized and self.cap is not None and self.cap.isOpened()
    
    def start_capture(self):
        """Start continuous frame capture in background thread"""
        if self.running:
            self.logger.warning("Capture already running")
            return
        
        if not self.is_ready():
            self.logger.error("Camera not ready")
            return
        
        self.running = True
        self.capture_thread = Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        self.logger.info("Camera capture started")
    
    def stop_capture(self):
        """Stop frame capture"""
        if self.running:
            self.running = False
            if self.capture_thread:
                self.capture_thread.join(timeout=2.0)
            self.logger.info("Camera capture stopped")
    
    def _capture_loop(self):
        """Background thread for continuous frame capture"""
        frame_count = 0
        last_fps_time = time.time()
        
        while self.running and self.cap.isOpened():
            ret, frame = self.cap.read()
            
            if not ret:
                self.logger.warning("Failed to read frame")
                time.sleep(0.1)
                continue
            
            # Update frame with thread safety
            with self.frame_lock:
                self.frame = frame
            
            # FPS monitoring
            frame_count += 1
            current_time = time.time()
            
            if current_time - last_fps_time >= 5.0:
                fps = frame_count / (current_time - last_fps_time)
                self.logger.debug(f"Camera capture FPS: {fps:.1f}")
                frame_count = 0
                last_fps_time = current_time
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Get latest frame
        
        Returns:
            Latest frame or None if not available
        """
        with self.frame_lock:
            if self.frame is not None:
                return self.frame.copy()
        return None
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Read frame directly from camera (blocking)
        
        Returns:
            Tuple of (success, frame)
        """
        if not self.is_ready():
            return False, None
        
        ret, frame = self.cap.read()
        return ret, frame if ret else None
