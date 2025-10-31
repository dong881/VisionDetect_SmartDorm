#!/usr/bin/env python3
"""
Health check script for VisionDetect SmartDorm
Checks system status and reports health metrics
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from visiondetect.core.config import get_config
from visiondetect.utils.logger import get_logger


def check_dependencies():
    """Check if all required dependencies are available"""
    dependencies = {
        'numpy': False,
        'cv2': False,
        'mediapipe': False,
        'yaml': False
    }
    
    for dep in dependencies:
        try:
            __import__(dep)
            dependencies[dep] = True
        except ImportError:
            dependencies[dep] = False
    
    return dependencies


def check_camera():
    """Check if camera is accessible"""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            cap.release()
            return True
        return False
    except Exception:
        return False


def check_gpio():
    """Check if GPIO is available"""
    try:
        import RPi.GPIO as GPIO
        return True
    except ImportError:
        return False


def check_configuration():
    """Check if configuration is valid"""
    try:
        config = get_config()
        required_keys = [
            'gpio.pin',
            'camera.device_id',
            'pose_detection.min_detection_confidence'
        ]
        
        for key in required_keys:
            if config.get(key) is None:
                return False
        
        return True
    except Exception:
        return False


def main():
    """Run health checks"""
    print("VisionDetect SmartDorm - Health Check")
    print("="*50)
    
    # Check dependencies
    print("\n[Dependencies]")
    deps = check_dependencies()
    for dep, available in deps.items():
        status = "✓" if available else "✗"
        print(f"  {status} {dep}")
    
    # Check camera
    print("\n[Hardware]")
    camera_ok = check_camera()
    print(f"  {'✓' if camera_ok else '✗'} Camera")
    
    gpio_ok = check_gpio()
    status_text = "Available" if gpio_ok else "Not available (mock mode)"
    print(f"  {'✓' if gpio_ok else '⚠'} GPIO - {status_text}")
    
    # Check configuration
    print("\n[Configuration]")
    config_ok = check_configuration()
    print(f"  {'✓' if config_ok else '✗'} Configuration file")
    
    # Overall status
    print("\n" + "="*50)
    
    all_deps_ok = all(deps.values())
    overall_ok = all_deps_ok and camera_ok and config_ok
    
    if overall_ok:
        print("✓ System is healthy and ready to run")
        return 0
    else:
        print("✗ System has issues that need to be resolved")
        
        if not all_deps_ok:
            print("\n  Please install missing dependencies:")
            print("    pip install -r requirements.txt")
        
        if not camera_ok:
            print("\n  Camera not accessible. Please check:")
            print("    - Camera is connected")
            print("    - Camera permissions are correct")
            print("    - Try: v4l2-ctl --list-devices")
        
        if not config_ok:
            print("\n  Configuration issues detected")
            print("    Check visiondetect/configs/default.yaml")
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
