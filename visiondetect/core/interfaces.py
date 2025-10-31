"""
Base interfaces for capability modules
Defines contracts for different system capabilities
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import numpy as np


class Capability(ABC):
    """Base class for all capability modules"""
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the capability
        
        Returns:
            True if initialization successful
        """
        pass
    
    @abstractmethod
    def cleanup(self):
        """Clean up resources"""
        pass
    
    @abstractmethod
    def is_ready(self) -> bool:
        """
        Check if capability is ready
        
        Returns:
            True if ready to use
        """
        pass


class Detector(Capability):
    """Base class for detection capabilities"""
    
    @abstractmethod
    def detect(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Perform detection on frame
        
        Args:
            frame: Input frame (BGR format)
            
        Returns:
            Detection results as dictionary
        """
        pass


class Controller(Capability):
    """Base class for control capabilities"""
    
    @abstractmethod
    def get_state(self) -> Any:
        """Get current state"""
        pass
    
    @abstractmethod
    def set_state(self, state: Any) -> bool:
        """
        Set new state
        
        Args:
            state: New state value
            
        Returns:
            True if state change successful
        """
        pass


class Notifier(Capability):
    """Base class for notification capabilities"""
    
    @abstractmethod
    def notify(self, message: str, **kwargs) -> bool:
        """
        Send notification
        
        Args:
            message: Notification message
            **kwargs: Additional parameters
            
        Returns:
            True if notification sent successfully
        """
        pass
