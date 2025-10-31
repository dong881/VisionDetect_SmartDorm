"""
Wake-on-LAN notifier capability
Sends WOL magic packets to wake target computers
"""

import os
import time
from typing import Optional, Any

from ..core.interfaces import Notifier
from ..core.config import get_config
from ..utils.logger import get_logger


class WOLNotifier(Notifier):
    """Wake-on-LAN notification sender"""
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize WOL notifier
        
        Args:
            config: Configuration object (uses global if None)
        """
        self.config = config or get_config()
        self.logger = get_logger()
        
        self.script_path = self.config.get('wol.script_path', './WOL.sh')
        self.cooldown = self.config.get('wol.cooldown', 90)
        self.last_wol_time = 0
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize WOL notifier"""
        try:
            # Check if WOL script exists
            if os.path.exists(self.script_path):
                self.logger.info(f"WOL notifier initialized (script: {self.script_path})")
                self._initialized = True
                return True
            else:
                self.logger.warning(f"WOL script not found: {self.script_path}")
                # Still initialize but with warning
                self._initialized = True
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to initialize WOL notifier: {e}")
            return False
    
    def cleanup(self):
        """Clean up resources"""
        self._initialized = False
        self.logger.info("WOL notifier cleaned up")
    
    def is_ready(self) -> bool:
        """Check if notifier is ready"""
        return self._initialized
    
    def notify(self, message: str = "WOL", **kwargs) -> bool:
        """
        Send WOL notification
        
        Args:
            message: Optional message (not used for WOL)
            **kwargs: Additional parameters
            
        Returns:
            True if WOL sent successfully
        """
        if not self.is_ready():
            self.logger.error("WOL notifier not ready")
            return False
        
        # Check cooldown
        current_time = time.time()
        time_since_last = current_time - self.last_wol_time
        
        if time_since_last < self.cooldown:
            remaining = int(self.cooldown - time_since_last)
            self.logger.info(f"WOL cooldown active. {remaining}s remaining")
            return False
        
        # Send WOL
        success = self._send_wol()
        
        if success:
            self.last_wol_time = current_time
            self.logger.info("WOL packet sent successfully")
        else:
            self.logger.error("Failed to send WOL packet")
        
        return success
    
    def _send_wol(self) -> bool:
        """
        Execute WOL script
        
        Returns:
            True if script executed successfully
        """
        try:
            if not os.path.exists(self.script_path):
                self.logger.error(f"WOL script not found: {self.script_path}")
                return False
            
            # Execute script
            result = os.system(self.script_path)
            
            if result == 0:
                return True
            else:
                self.logger.error(f"WOL script failed with exit code: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing WOL script: {e}")
            return False
    
    def can_send(self) -> bool:
        """
        Check if WOL can be sent (not in cooldown)
        
        Returns:
            True if can send
        """
        current_time = time.time()
        return (current_time - self.last_wol_time) >= self.cooldown
    
    def get_cooldown_remaining(self) -> int:
        """
        Get remaining cooldown time
        
        Returns:
            Seconds remaining in cooldown, or 0 if ready
        """
        current_time = time.time()
        elapsed = current_time - self.last_wol_time
        remaining = self.cooldown - elapsed
        
        return max(0, int(remaining))
