"""
GPIO light controller capability
Controls lights via Raspberry Pi GPIO
"""

from typing import Optional, Any
import time

from ..core.interfaces import Controller
from ..core.config import get_config
from ..utils.logger import get_logger

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False


class LightController(Controller):
    """Controls lights via GPIO"""
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize light controller
        
        Args:
            config: Configuration object (uses global if None)
        """
        self.config = config or get_config()
        self.logger = get_logger()
        
        self.gpio_pin = self.config.get('gpio.pin', 18)
        self.gpio_mode_str = self.config.get('gpio.mode', 'BCM')
        
        self.current_state = False
        self.target_state = False
        self._initialized = False
        
        if not GPIO_AVAILABLE:
            self.logger.warning("RPi.GPIO not available - light control disabled")
    
    def initialize(self) -> bool:
        """Initialize GPIO"""
        if not GPIO_AVAILABLE:
            self.logger.warning("GPIO not available, using mock mode")
            self._initialized = True
            return True
        
        try:
            # Set GPIO mode
            GPIO.setwarnings(False)
            
            if self.gpio_mode_str.upper() == 'BCM':
                GPIO.setmode(GPIO.BCM)
            else:
                GPIO.setmode(GPIO.BOARD)
            
            # Setup pin
            GPIO.setup(self.gpio_pin, GPIO.OUT)
            GPIO.output(self.gpio_pin, GPIO.LOW)
            
            self.current_state = False
            self.target_state = False
            
            self._initialized = True
            self.logger.info(f"GPIO light controller initialized (pin: {self.gpio_pin})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize GPIO: {e}")
            return False
    
    def cleanup(self):
        """Clean up GPIO resources"""
        if GPIO_AVAILABLE and self._initialized:
            try:
                GPIO.cleanup()
                self.logger.info("GPIO cleaned up")
            except Exception as e:
                self.logger.error(f"Error cleaning up GPIO: {e}")
        
        self._initialized = False
    
    def is_ready(self) -> bool:
        """Check if controller is ready"""
        return self._initialized
    
    def get_state(self) -> bool:
        """
        Get current light state
        
        Returns:
            True if light is on, False otherwise
        """
        return self.current_state
    
    def set_state(self, state: bool) -> bool:
        """
        Set light state
        
        Args:
            state: True to turn on, False to turn off
            
        Returns:
            True if state change successful
        """
        if not self.is_ready():
            return False
        
        try:
            if state != self.current_state:
                if GPIO_AVAILABLE:
                    GPIO.output(self.gpio_pin, GPIO.HIGH if state else GPIO.LOW)
                
                self.current_state = state
                self.logger.info(f"Light {'ON' if state else 'OFF'}")
                return True
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting GPIO state: {e}")
            return False
    
    def set_target_state(self, state: bool):
        """
        Set target state (may be applied later)
        
        Args:
            state: Target state
        """
        self.target_state = state
    
    def apply_target_state(self) -> bool:
        """
        Apply target state to actual GPIO
        
        Returns:
            True if state changed
        """
        if self.target_state != self.current_state:
            return self.set_state(self.target_state)
        return False


class LightScheduler:
    """Manages light control logic with timing"""
    
    def __init__(self, controller: LightController, config: Optional[Any] = None):
        """
        Initialize light scheduler
        
        Args:
            controller: Light controller instance
            config: Configuration object
        """
        self.controller = controller
        self.config = config or get_config()
        self.logger = get_logger()
        
        self.last_detection_time = 0
        self.person_present = False
        
        # Load delays from config
        self.day_start = self.config.get('light_control.day_start_hour', 8)
        self.day_end = self.config.get('light_control.day_end_hour', 22)
        self.day_delay = self.config.get('light_control.off_delay.day', 300)
        self.night_delay = self.config.get('light_control.off_delay.night', 180)
    
    def is_daytime(self) -> bool:
        """Check if current time is daytime"""
        from datetime import datetime
        current_hour = datetime.now().hour
        return self.day_start <= current_hour < self.day_end
    
    def get_off_delay(self) -> int:
        """Get current off delay based on time of day"""
        return self.day_delay if self.is_daytime() else self.night_delay
    
    def update(self, person_detected: bool, current_time: Optional[float] = None):
        """
        Update light state based on person detection
        
        Args:
            person_detected: Whether person is detected
            current_time: Current timestamp (uses time.time() if None)
        """
        if current_time is None:
            current_time = time.time()
        
        if person_detected:
            # Person detected - turn light on
            self.last_detection_time = current_time
            self.person_present = True
            self.controller.set_target_state(True)
        else:
            # No person detected
            self.person_present = False
            
            # Check if we should turn off
            time_since_detection = current_time - self.last_detection_time
            off_delay = self.get_off_delay()
            
            if time_since_detection > off_delay:
                self.controller.set_target_state(False)
        
        # Apply the target state
        self.controller.apply_target_state()
    
    def get_time_until_off(self) -> float:
        """
        Get time remaining until light turns off
        
        Returns:
            Seconds until off, or 0 if light should be off
        """
        if self.person_present:
            return float('inf')
        
        time_since = time.time() - self.last_detection_time
        off_delay = self.get_off_delay()
        remaining = off_delay - time_since
        
        return max(0, remaining)
