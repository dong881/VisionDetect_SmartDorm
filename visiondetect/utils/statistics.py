"""
Statistics and metrics tracking module
Tracks system performance and detection statistics
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List
from collections import deque
from threading import Lock


@dataclass
class DetectionStats:
    """Statistics for detection operations"""
    total_frames: int = 0
    frames_with_person: int = 0
    frames_without_person: int = 0
    gesture_detections: int = 0
    wol_triggers: int = 0
    light_on_count: int = 0
    light_off_count: int = 0
    errors: int = 0
    start_time: float = field(default_factory=time.time)
    
    @property
    def uptime_seconds(self) -> float:
        """Get system uptime in seconds"""
        return time.time() - self.start_time
    
    @property
    def person_detection_rate(self) -> float:
        """Get percentage of frames with person detected"""
        if self.total_frames == 0:
            return 0.0
        return (self.frames_with_person / self.total_frames) * 100
    
    def to_dict(self) -> Dict:
        """Convert statistics to dictionary"""
        return {
            'total_frames': self.total_frames,
            'frames_with_person': self.frames_with_person,
            'frames_without_person': self.frames_without_person,
            'gesture_detections': self.gesture_detections,
            'wol_triggers': self.wol_triggers,
            'light_on_count': self.light_on_count,
            'light_off_count': self.light_off_count,
            'errors': self.errors,
            'uptime_seconds': self.uptime_seconds,
            'person_detection_rate': self.person_detection_rate
        }


class PerformanceMonitor:
    """Monitor and track system performance metrics"""
    
    def __init__(self, window_size: int = 100):
        """
        Initialize performance monitor
        
        Args:
            window_size: Number of samples to keep for moving averages
        """
        self.window_size = window_size
        self.frame_times = deque(maxlen=window_size)
        self.processing_times = deque(maxlen=window_size)
        self.lock = Lock()
        
        self.last_fps_report = time.time()
        self.frames_since_report = 0
    
    def record_frame_time(self, duration: float):
        """Record time taken to capture a frame"""
        with self.lock:
            self.frame_times.append(duration)
    
    def record_processing_time(self, duration: float):
        """Record time taken to process a frame"""
        with self.lock:
            self.processing_times.append(duration)
            self.frames_since_report += 1
    
    def get_fps(self, window: str = "capture") -> float:
        """
        Get frames per second
        
        Args:
            window: 'capture' for capture FPS, 'processing' for processing FPS
            
        Returns:
            Current FPS
        """
        with self.lock:
            times = self.frame_times if window == "capture" else self.processing_times
            
            if len(times) < 2:
                return 0.0
            
            avg_time = sum(times) / len(times)
            if avg_time <= 0:
                return 0.0
            
            return 1.0 / avg_time
    
    def get_average_processing_time(self) -> float:
        """Get average processing time in milliseconds"""
        with self.lock:
            if not self.processing_times:
                return 0.0
            return (sum(self.processing_times) / len(self.processing_times)) * 1000
    
    def should_report_fps(self, interval: float = 5.0) -> bool:
        """
        Check if it's time to report FPS
        
        Args:
            interval: Report interval in seconds
            
        Returns:
            True if should report
        """
        current_time = time.time()
        if current_time - self.last_fps_report >= interval:
            with self.lock:
                self.last_fps_report = current_time
                self.frames_since_report = 0
            return True
        return False
    
    def get_stats(self) -> Dict:
        """Get performance statistics"""
        return {
            'capture_fps': round(self.get_fps('capture'), 2),
            'processing_fps': round(self.get_fps('processing'), 2),
            'avg_processing_time_ms': round(self.get_average_processing_time(), 2),
            'frames_in_window': len(self.processing_times)
        }


class StatisticsManager:
    """Global statistics manager"""
    
    def __init__(self):
        self.detection_stats = DetectionStats()
        self.performance = PerformanceMonitor()
        self.lock = Lock()
    
    def increment_total_frames(self):
        """Increment total frame count"""
        with self.lock:
            self.detection_stats.total_frames += 1
    
    def record_person_detected(self, detected: bool):
        """Record person detection result"""
        with self.lock:
            if detected:
                self.detection_stats.frames_with_person += 1
            else:
                self.detection_stats.frames_without_person += 1
    
    def record_gesture_detection(self):
        """Record gesture detection"""
        with self.lock:
            self.detection_stats.gesture_detections += 1
    
    def record_wol_trigger(self):
        """Record WOL trigger"""
        with self.lock:
            self.detection_stats.wol_triggers += 1
    
    def record_light_change(self, turned_on: bool):
        """Record light state change"""
        with self.lock:
            if turned_on:
                self.detection_stats.light_on_count += 1
            else:
                self.detection_stats.light_off_count += 1
    
    def record_error(self):
        """Record error"""
        with self.lock:
            self.detection_stats.errors += 1
    
    def get_summary(self) -> Dict:
        """Get complete statistics summary"""
        with self.lock:
            summary = {
                'detection': self.detection_stats.to_dict(),
                'performance': self.performance.get_stats()
            }
        return summary


# Global statistics instance
_stats_instance = None


def get_statistics() -> StatisticsManager:
    """Get global statistics manager instance"""
    global _stats_instance
    if _stats_instance is None:
        _stats_instance = StatisticsManager()
    return _stats_instance
