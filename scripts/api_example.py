#!/usr/bin/env python3
"""
Example script demonstrating API usage
Shows how to interact with VisionDetect SmartDorm remotely
"""

import requests
import time
import json


class SmartDormClient:
    """Client for interacting with VisionDetect SmartDorm API"""
    
    def __init__(self, base_url="http://localhost:8080"):
        """
        Initialize client
        
        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url.rstrip('/')
    
    def get_status(self):
        """Get system status"""
        response = requests.get(f"{self.base_url}/api/status")
        response.raise_for_status()
        return response.json()
    
    def get_statistics(self):
        """Get statistics"""
        response = requests.get(f"{self.base_url}/api/statistics")
        response.raise_for_status()
        return response.json()
    
    def get_health(self):
        """Get health status"""
        response = requests.get(f"{self.base_url}/api/health")
        response.raise_for_status()
        return response.json()
    
    def get_light_state(self):
        """Get light state"""
        response = requests.get(f"{self.base_url}/api/light")
        response.raise_for_status()
        return response.json()
    
    def set_light_state(self, state):
        """
        Set light state
        
        Args:
            state: True for on, False for off
        """
        response = requests.post(
            f"{self.base_url}/api/light",
            json={"state": state},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    
    def trigger_wol(self):
        """Trigger Wake-on-LAN"""
        response = requests.post(f"{self.base_url}/api/wol")
        response.raise_for_status()
        return response.json()


def example_monitoring():
    """Example: Monitor system status"""
    print("=== System Monitoring Example ===\n")
    
    client = SmartDormClient()
    
    try:
        # Get system status
        status = client.get_status()
        data = status['data']
        
        print("System Status:")
        print(f"  Running: {data['running']}")
        print(f"  Person Present: {data['person_present']}")
        print(f"  Light State: {'ON' if data['light_state'] else 'OFF'}")
        print(f"  Time until light off: {data['time_until_light_off']:.0f}s")
        print()
        
        # Get statistics
        stats = client.get_statistics()
        detection = stats['data']['detection']
        performance = stats['data']['performance']
        
        print("Statistics:")
        print(f"  Total Frames: {detection['total_frames']}")
        print(f"  Detection Rate: {detection['person_detection_rate']:.1f}%")
        print(f"  Gesture Detections: {detection['gesture_detections']}")
        print(f"  WOL Triggers: {detection['wol_triggers']}")
        print(f"  Processing FPS: {performance['processing_fps']}")
        print(f"  Avg Processing Time: {performance['avg_processing_time_ms']:.1f}ms")
        print()
        
        # Get health
        health = client.get_health()
        print("Health Status:")
        print(f"  Status: {health['status']}")
        print(f"  Camera: {'✓' if health['capabilities']['camera'] else '✗'}")
        print(f"  Pose Detector: {'✓' if health['capabilities']['pose_detector'] else '✗'}")
        print(f"  Hand Detector: {'✓' if health['capabilities']['hand_detector'] else '✗'}")
        print(f"  Light Controller: {'✓' if health['capabilities']['light_controller'] else '✗'}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        print("Make sure the API server is running with --enable-api flag")


def example_light_control():
    """Example: Control light"""
    print("\n=== Light Control Example ===\n")
    
    client = SmartDormClient()
    
    try:
        # Get current state
        light_status = client.get_light_state()
        current_state = light_status['data']['light_on']
        print(f"Current light state: {'ON' if current_state else 'OFF'}")
        
        # Toggle light
        new_state = not current_state
        print(f"Setting light to: {'ON' if new_state else 'OFF'}")
        
        result = client.set_light_state(new_state)
        print(f"Result: {result['message']}")
        
        # Wait a bit
        time.sleep(2)
        
        # Restore original state
        print(f"Restoring light to: {'ON' if current_state else 'OFF'}")
        result = client.set_light_state(current_state)
        print(f"Result: {result['message']}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")


def example_wol():
    """Example: Trigger Wake-on-LAN"""
    print("\n=== Wake-on-LAN Example ===\n")
    
    client = SmartDormClient()
    
    try:
        result = client.trigger_wol()
        print(f"WOL Result: {result['message']}")
        
        if 'cooldown_remaining' in result.get('data', {}):
            print(f"Cooldown remaining: {result['data']['cooldown_remaining']}s")
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")


def example_continuous_monitoring():
    """Example: Continuous monitoring with updates"""
    print("\n=== Continuous Monitoring Example ===\n")
    print("Monitoring system status (Press Ctrl+C to stop)...\n")
    
    client = SmartDormClient()
    
    try:
        while True:
            try:
                status = client.get_status()
                data = status['data']
                
                # Clear line and print status
                person_status = "Person DETECTED" if data['person_present'] else "No person"
                light_status = "Light ON" if data['light_state'] else "Light OFF"
                
                print(f"\r{person_status:20} | {light_status:12} | "
                      f"Time until off: {data['time_until_light_off']:6.0f}s", 
                      end='', flush=True)
                
                time.sleep(1)
                
            except requests.exceptions.RequestException:
                print("\rConnection error - retrying...", end='', flush=True)
                time.sleep(2)
    
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped")


def main():
    """Main function"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "monitor":
            example_monitoring()
        elif command == "light":
            example_light_control()
        elif command == "wol":
            example_wol()
        elif command == "continuous":
            example_continuous_monitoring()
        else:
            print(f"Unknown command: {command}")
            print_usage()
    else:
        # Run all examples
        example_monitoring()
        example_light_control()
        example_wol()
        
        # Ask if user wants continuous monitoring
        response = input("\nRun continuous monitoring? (y/n): ")
        if response.lower() == 'y':
            example_continuous_monitoring()


def print_usage():
    """Print usage information"""
    print("Usage: python api_example.py [command]")
    print()
    print("Commands:")
    print("  monitor      - Get system status and statistics once")
    print("  light        - Demonstrate light control")
    print("  wol          - Trigger Wake-on-LAN")
    print("  continuous   - Continuous status monitoring")
    print("  (no command) - Run all examples")
    print()
    print("Examples:")
    print("  python api_example.py monitor")
    print("  python api_example.py continuous")


if __name__ == "__main__":
    main()
