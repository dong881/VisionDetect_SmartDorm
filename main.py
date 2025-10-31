#!/usr/bin/env python3
"""
VisionDetect SmartDorm - Main Entry Point
Intelligent dormitory vision detection system with pose and gesture recognition
"""

import sys
import signal
import time
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from visiondetect.core.orchestrator import SmartDormOrchestrator
from visiondetect.utils.logger import get_logger


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\nReceived shutdown signal. Exiting gracefully...")
    sys.exit(0)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="VisionDetect SmartDorm - Intelligent dormitory vision detection"
    )
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Path to configuration file (default: use built-in config)'
    )
    parser.add_argument(
        '--status-interval',
        type=int,
        default=10,
        help='Status report interval in seconds (default: 10)'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    parser.add_argument(
        '--enable-api',
        action='store_true',
        help='Enable HTTP API server for remote monitoring'
    )
    parser.add_argument(
        '--api-port',
        type=int,
        default=8080,
        help='API server port (default: 8080)'
    )
    
    args = parser.parse_args()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create orchestrator
    orchestrator = SmartDormOrchestrator(config_path=args.config)
    logger = get_logger()
    
    # Optionally create API server
    api_server = None
    if args.enable_api:
        from visiondetect.utils.api import APIServer
        api_server = APIServer(orchestrator, port=args.api_port)
    
    try:
        # Initialize all capabilities
        logger.info("="*50)
        logger.info("VisionDetect SmartDorm v2.0.0")
        logger.info("="*50)
        
        if not orchestrator.initialize_all():
            logger.error("Failed to initialize system")
            return 1
        
        # Start the system
        orchestrator.start()
        
        # Start API server if enabled
        if api_server:
            api_server.start()
            logger.info(f"API available at http://localhost:{args.api_port}/api")
        
        # Main status loop
        logger.info("System running. Press Ctrl+C to exit.")
        logger.info("-"*50)
        
        while True:
            time.sleep(args.status_interval)
            orchestrator.print_status()
    
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1
    
    finally:
        # Clean shutdown
        logger.info("Shutting down...")
        
        # Stop API server
        if api_server:
            api_server.stop()
        
        orchestrator.stop()
        orchestrator.cleanup_all()
        
        # Print final statistics
        stats = orchestrator.stats.get_summary()
        logger.info("-"*50)
        logger.info("Final Statistics:")
        logger.info(f"  Total frames processed: {stats['detection']['total_frames']}")
        logger.info(f"  Person detection rate: {stats['detection']['person_detection_rate']:.1f}%")
        logger.info(f"  Gesture detections: {stats['detection']['gesture_detections']}")
        logger.info(f"  WOL triggers: {stats['detection']['wol_triggers']}")
        logger.info(f"  Light changes: {stats['detection']['light_on_count'] + stats['detection']['light_off_count']}")
        logger.info(f"  Errors: {stats['detection']['errors']}")
        logger.info(f"  Uptime: {stats['detection']['uptime_seconds']:.1f}s")
        logger.info("="*50)
        logger.info("Shutdown complete")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
