"""
Core orchestrator module
Coordinates all capabilities and manages the main detection loop
"""

import time
from typing import Optional
from collections import deque
from threading import Thread, Event

from ..core.config import get_config
from ..utils.logger import get_logger
from ..utils.statistics import get_statistics
from ..capabilities.camera import CameraCapture
from ..capabilities.pose_detection import PoseDetector
from ..capabilities.hand_gesture import HandGestureDetector
from ..capabilities.light_control import LightController, LightScheduler
from ..capabilities.wol import WOLNotifier


class SmartDormOrchestrator:
    """Main orchestrator for SmartDorm system"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize orchestrator
        
        Args:
            config_path: Path to configuration file
        """
        # Initialize configuration and utilities
        self.config = get_config(config_path)
        self.logger = get_logger(
            log_dir=self.config.log_dir,
            log_level=self.config.log_level
        )
        self.stats = get_statistics()
        
        # Initialize capabilities
        self.camera = CameraCapture(self.config)
        self.pose_detector = PoseDetector(self.config)
        self.hand_detector = HandGestureDetector(self.config)
        self.light_controller = LightController(self.config)
        self.light_scheduler = LightScheduler(self.light_controller, self.config)
        self.wol_notifier = WOLNotifier(self.config)
        
        # Detection state
        self.presence_buffer = deque(
            maxlen=self.config.get('presence.buffer_size', 5)
        )
        self.presence_threshold = self.config.get('presence.threshold', 0.7)
        
        # Control flags
        self.running = False
        self.stop_event = Event()
        self.processing_thread = None
        
        self.logger.info("SmartDorm Orchestrator initialized")
    
    def initialize_all(self) -> bool:
        """
        Initialize all capabilities
        
        Returns:
            True if all initialized successfully
        """
        self.logger.info("Initializing all capabilities...")
        
        results = {
            'camera': self.camera.initialize(),
            'pose_detector': self.pose_detector.initialize(),
            'hand_detector': self.hand_detector.initialize(),
            'light_controller': self.light_controller.initialize(),
            'wol_notifier': self.wol_notifier.initialize()
        }
        
        # Log results
        for name, success in results.items():
            status = "✓" if success else "✗"
            self.logger.info(f"{status} {name}: {'initialized' if success else 'failed'}")
        
        all_success = all(results.values())
        
        if all_success:
            self.logger.info("All capabilities initialized successfully")
        else:
            self.logger.error("Some capabilities failed to initialize")
        
        return all_success
    
    def cleanup_all(self):
        """Clean up all capabilities"""
        self.logger.info("Cleaning up all capabilities...")
        
        self.camera.cleanup()
        self.pose_detector.cleanup()
        self.hand_detector.cleanup()
        self.light_controller.cleanup()
        self.wol_notifier.cleanup()
        
        self.logger.info("Cleanup complete")
    
    def start(self):
        """Start the detection system"""
        if self.running:
            self.logger.warning("System already running")
            return
        
        self.logger.info("Starting SmartDorm system...")
        
        # Start camera capture
        self.camera.start_capture()
        
        # Start processing thread
        self.running = True
        self.stop_event.clear()
        self.processing_thread = Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        
        self.logger.info("SmartDorm system started")
    
    def stop(self):
        """Stop the detection system"""
        if not self.running:
            return
        
        self.logger.info("Stopping SmartDorm system...")
        
        self.running = False
        self.stop_event.set()
        
        # Stop camera
        self.camera.stop_capture()
        
        # Wait for processing thread
        if self.processing_thread:
            self.processing_thread.join(timeout=5.0)
        
        self.logger.info("SmartDorm system stopped")
    
    def _processing_loop(self):
        """Main processing loop"""
        self.logger.info("Processing loop started")
        
        fps_report_interval = self.config.get('performance.fps_report_interval', 5)
        enable_hand_gesture = self.config.get('features.enable_hand_gesture', True)
        enable_wol = self.config.get('features.enable_wol', True)
        
        while self.running and not self.stop_event.is_set():
            try:
                start_time = time.time()
                
                # Get frame
                frame = self.camera.get_frame()
                
                if frame is None:
                    time.sleep(0.01)
                    continue
                
                # Perform pose detection
                pose_results = self.pose_detector.detect(frame)
                pose_confidence = pose_results['confidence']
                person_detected = pose_results['present']
                
                # Update presence buffer for smoothing
                self.presence_buffer.append(person_detected)
                presence_ratio = sum(self.presence_buffer) / len(self.presence_buffer)
                
                # Determine if person is present
                person_present = presence_ratio >= self.presence_threshold
                
                # Update statistics
                self.stats.increment_total_frames()
                self.stats.record_person_detected(person_present)
                
                # Perform hand gesture detection if person present and enabled
                if enable_hand_gesture and person_present:
                    hand_results = self.hand_detector.detect(frame)
                    gesture_confidence = hand_results['gesture_confidence']
                    
                    # Update gesture state
                    if gesture_confidence > 0:
                        gesture_confirmed = self.hand_detector.update_gesture_state(
                            gesture_confidence,
                            time.time()
                        )
                        
                        # Trigger WOL if gesture confirmed
                        if gesture_confirmed and enable_wol:
                            self.stats.record_gesture_detection()
                            
                            # Send WOL in separate thread
                            Thread(target=self._trigger_wol, daemon=True).start()
                            
                            # Reset gesture state
                            self.hand_detector.reset_gesture_state()
                
                # Update light control
                self.light_scheduler.update(person_present)
                
                # Record processing time
                processing_time = time.time() - start_time
                self.stats.performance.record_processing_time(processing_time)
                
                # Report FPS periodically
                if self.stats.performance.should_report_fps(fps_report_interval):
                    perf_stats = self.stats.performance.get_stats()
                    self.logger.info(
                        f"Performance: Processing FPS={perf_stats['processing_fps']}, "
                        f"Avg Time={perf_stats['avg_processing_time_ms']:.1f}ms"
                    )
                
            except Exception as e:
                self.logger.error(f"Error in processing loop: {e}", exc_info=True)
                self.stats.record_error()
                time.sleep(0.1)
        
        self.logger.info("Processing loop stopped")
    
    def _trigger_wol(self):
        """Trigger WOL notification (runs in separate thread)"""
        try:
            if self.wol_notifier.can_send():
                success = self.wol_notifier.notify()
                if success:
                    self.stats.record_wol_trigger()
        except Exception as e:
            self.logger.error(f"Error triggering WOL: {e}")
    
    def get_status(self) -> dict:
        """
        Get current system status
        
        Returns:
            Dictionary with system status
        """
        return {
            'running': self.running,
            'camera_ready': self.camera.is_ready(),
            'pose_detector_ready': self.pose_detector.is_ready(),
            'hand_detector_ready': self.hand_detector.is_ready(),
            'light_controller_ready': self.light_controller.is_ready(),
            'light_state': self.light_controller.get_state(),
            'person_present': self.light_scheduler.person_present,
            'time_until_light_off': self.light_scheduler.get_time_until_off(),
            'wol_cooldown_remaining': self.wol_notifier.get_cooldown_remaining(),
            'statistics': self.stats.get_summary()
        }
    
    def print_status(self):
        """Print current status to console"""
        status = self.get_status()
        
        light_state = "ON" if status['light_state'] else "OFF"
        person = "YES" if status['person_present'] else "NO"
        
        if status['person_present']:
            self.logger.info(f"Status: Person detected. Light: {light_state}")
        else:
            time_left = status['time_until_light_off']
            if time_left > 0 and time_left < float('inf'):
                self.logger.info(
                    f"Status: No person. Light will turn off in {int(time_left)}s"
                )
            else:
                self.logger.info(f"Status: No person detected. Light: {light_state}")
