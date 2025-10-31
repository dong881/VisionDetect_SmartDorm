"""
Simple HTTP API for remote monitoring and control
Provides REST endpoints to query system status and statistics
"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Optional
import threading

from ..utils.logger import get_logger


class APIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for API endpoints"""
    
    # Reference to orchestrator (set by APIServer)
    orchestrator = None
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger = get_logger()
        logger.debug(f"{self.address_string()} - {format % args}")
    
    def _set_headers(self, status=200, content_type='application/json'):
        """Set response headers"""
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def _send_json(self, data, status=200):
        """Send JSON response"""
        self._set_headers(status)
        response = json.dumps(data, indent=2, ensure_ascii=False)
        self.wfile.write(response.encode('utf-8'))
    
    def _send_error(self, message, status=400):
        """Send error response"""
        self._send_json({'error': message, 'status': 'error'}, status)
    
    def do_OPTIONS(self):
        """Handle OPTIONS request for CORS"""
        self._set_headers(204)
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if not self.orchestrator:
            self._send_error("Orchestrator not available", 503)
            return
        
        try:
            if path == '/' or path == '/api':
                self._handle_root()
            elif path == '/api/status':
                self._handle_status()
            elif path == '/api/statistics':
                self._handle_statistics()
            elif path == '/api/health':
                self._handle_health()
            elif path == '/api/light':
                self._handle_light_get()
            else:
                self._send_error("Endpoint not found", 404)
        
        except Exception as e:
            logger = get_logger()
            logger.error(f"API error: {e}", exc_info=True)
            self._send_error(f"Internal server error: {str(e)}", 500)
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if not self.orchestrator:
            self._send_error("Orchestrator not available", 503)
            return
        
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            if body:
                data = json.loads(body.decode('utf-8'))
            else:
                data = {}
            
            if path == '/api/light':
                self._handle_light_post(data)
            elif path == '/api/wol':
                self._handle_wol_post(data)
            else:
                self._send_error("Endpoint not found", 404)
        
        except json.JSONDecodeError:
            self._send_error("Invalid JSON", 400)
        except Exception as e:
            logger = get_logger()
            logger.error(f"API error: {e}", exc_info=True)
            self._send_error(f"Internal server error: {str(e)}", 500)
    
    def _handle_root(self):
        """Handle root endpoint - API info"""
        info = {
            'name': 'VisionDetect SmartDorm API',
            'version': '2.0.0',
            'endpoints': {
                'GET /api': 'API information',
                'GET /api/status': 'System status',
                'GET /api/statistics': 'Statistics and metrics',
                'GET /api/health': 'Health check',
                'GET /api/light': 'Get light state',
                'POST /api/light': 'Control light (body: {"state": true/false})',
                'POST /api/wol': 'Trigger Wake-on-LAN'
            }
        }
        self._send_json(info)
    
    def _handle_status(self):
        """Handle status endpoint"""
        status = self.orchestrator.get_status()
        self._send_json({
            'status': 'ok',
            'data': status
        })
    
    def _handle_statistics(self):
        """Handle statistics endpoint"""
        stats = self.orchestrator.stats.get_summary()
        self._send_json({
            'status': 'ok',
            'data': stats
        })
    
    def _handle_health(self):
        """Handle health check endpoint"""
        status = self.orchestrator.get_status()
        
        all_ready = (
            status['camera_ready'] and
            status['pose_detector_ready'] and
            status['hand_detector_ready'] and
            status['light_controller_ready']
        )
        
        health = {
            'status': 'healthy' if all_ready else 'degraded',
            'running': status['running'],
            'capabilities': {
                'camera': status['camera_ready'],
                'pose_detector': status['pose_detector_ready'],
                'hand_detector': status['hand_detector_ready'],
                'light_controller': status['light_controller_ready']
            }
        }
        
        self._send_json(health)
    
    def _handle_light_get(self):
        """Handle GET light state"""
        state = self.orchestrator.light_controller.get_state()
        self._send_json({
            'status': 'ok',
            'data': {
                'light_on': state,
                'person_present': self.orchestrator.light_scheduler.person_present,
                'time_until_off': self.orchestrator.light_scheduler.get_time_until_off()
            }
        })
    
    def _handle_light_post(self, data):
        """Handle POST light control"""
        if 'state' not in data:
            self._send_error("Missing 'state' field", 400)
            return
        
        state = bool(data['state'])
        success = self.orchestrator.light_controller.set_state(state)
        
        if success:
            self._send_json({
                'status': 'ok',
                'message': f"Light turned {'on' if state else 'off'}",
                'data': {'light_on': state}
            })
        else:
            self._send_error("Failed to control light", 500)
    
    def _handle_wol_post(self, data):
        """Handle POST WOL trigger"""
        if self.orchestrator.wol_notifier.can_send():
            success = self.orchestrator.wol_notifier.notify()
            
            if success:
                self._send_json({
                    'status': 'ok',
                    'message': 'WOL packet sent',
                    'data': {'sent': True}
                })
            else:
                self._send_error("Failed to send WOL packet", 500)
        else:
            remaining = self.orchestrator.wol_notifier.get_cooldown_remaining()
            self._send_json({
                'status': 'ok',
                'message': f'WOL in cooldown, {remaining}s remaining',
                'data': {
                    'sent': False,
                    'cooldown_remaining': remaining
                }
            })


class APIServer:
    """HTTP API server for remote monitoring and control"""
    
    def __init__(self, orchestrator, host='0.0.0.0', port=8080):
        """
        Initialize API server
        
        Args:
            orchestrator: SmartDormOrchestrator instance
            host: Host to bind to
            port: Port to bind to
        """
        self.orchestrator = orchestrator
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None
        self.running = False
        self.logger = get_logger()
    
    def start(self):
        """Start API server in background thread"""
        if self.running:
            self.logger.warning("API server already running")
            return
        
        try:
            # Set orchestrator reference for handler
            APIHandler.orchestrator = self.orchestrator
            
            # Create server
            self.server = HTTPServer((self.host, self.port), APIHandler)
            
            # Start in thread
            self.running = True
            self.server_thread = threading.Thread(
                target=self._serve_forever,
                daemon=True
            )
            self.server_thread.start()
            
            self.logger.info(f"API server started on http://{self.host}:{self.port}")
        
        except Exception as e:
            self.logger.error(f"Failed to start API server: {e}")
            self.running = False
    
    def _serve_forever(self):
        """Serve requests in background"""
        try:
            self.server.serve_forever()
        except Exception as e:
            self.logger.error(f"API server error: {e}")
        finally:
            self.running = False
    
    def stop(self):
        """Stop API server"""
        if not self.running:
            return
        
        self.logger.info("Stopping API server...")
        self.running = False
        
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        
        if self.server_thread:
            self.server_thread.join(timeout=5.0)
        
        self.logger.info("API server stopped")
