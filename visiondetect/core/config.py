"""
Configuration management module
Handles loading and validation of configuration files
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """Configuration manager for VisionDetect SmartDorm"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration
        
        Args:
            config_path: Path to configuration file. If None, uses default config.
        """
        if config_path is None:
            # Use default config from same directory
            config_dir = Path(__file__).parent.parent / "configs"
            config_path = config_dir / "default.yaml"
        
        self._config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file"""
        if not self._config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self._config_path}")
        
        with open(self._config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        
        Args:
            key_path: Configuration key path (e.g., 'gpio.pin')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """
        Set configuration value using dot notation
        
        Args:
            key_path: Configuration key path (e.g., 'gpio.pin')
            value: Value to set
        """
        keys = key_path.split('.')
        config = self._config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def reload(self):
        """Reload configuration from file"""
        self._load_config()
    
    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary"""
        return self._config.copy()
    
    @property
    def gpio_pin(self) -> int:
        """GPIO pin number"""
        return self.get('gpio.pin', 18)
    
    @property
    def camera_device_id(self) -> int:
        """Camera device ID"""
        return self.get('camera.device_id', 0)
    
    @property
    def camera_width(self) -> int:
        """Camera width"""
        return self.get('camera.width', 640)
    
    @property
    def camera_height(self) -> int:
        """Camera height"""
        return self.get('camera.height', 480)
    
    @property
    def log_level(self) -> str:
        """Log level"""
        return self.get('system.log_level', 'INFO')
    
    @property
    def log_dir(self) -> str:
        """Log directory"""
        return self.get('system.log_dir', 'LOG')


# Global configuration instance
_config_instance: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """
    Get global configuration instance
    
    Args:
        config_path: Path to configuration file (only used on first call)
        
    Returns:
        Configuration instance
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = Config(config_path)
    
    return _config_instance


def reload_config():
    """Reload global configuration"""
    global _config_instance
    
    if _config_instance is not None:
        _config_instance.reload()
