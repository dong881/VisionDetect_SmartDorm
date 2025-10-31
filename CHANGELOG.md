# Changelog

All notable changes to VisionDetect SmartDorm will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-01-31

### Added

#### Architecture
- **Modular Architecture**: Complete restructuring into modules (core, capabilities, utils, configs)
- **Standard Interfaces**: Base classes for Capability, Detector, Controller, and Notifier
- **Configuration Management**: YAML-based configuration with dot notation access
- **Orchestrator Pattern**: Central coordinator managing all capabilities lifecycle

#### Capabilities
- **Camera Capture**: Threaded camera capture with separate capture and processing threads
- **Pose Detection**: Enhanced MediaPipe pose detection with confidence scoring
- **Hand Gesture**: Improved gesture recognition with state machine
- **Light Control**: Refactored GPIO control with scheduler and time-based delays
- **Wake-on-LAN**: Modular WOL notifier with cooldown management

#### Features
- **Web API Server**: HTTP REST API for remote monitoring and control
  - GET /api/status - System status
  - GET /api/statistics - Performance and detection statistics
  - GET /api/health - Health check
  - GET /api/light - Light state
  - POST /api/light - Control light
  - POST /api/wol - Trigger Wake-on-LAN
- **Health Check Script**: Comprehensive system health verification tool
- **API Client Example**: Example script demonstrating API usage
- **Structured Logging**: Enhanced logging with file rotation and log levels
- **Performance Monitoring**: Real-time FPS tracking and processing time metrics
- **Statistics Tracking**: Comprehensive statistics collection
  - Total frames processed
  - Person detection rate
  - Gesture detection count
  - WOL trigger count
  - Light state changes
  - Error count
  - System uptime

#### Developer Experience
- **Enhanced Documentation**: New ARCHITECTURE.md with detailed design documentation
- **Command-line Interface**: Rich CLI with multiple options
  - Custom config file support
  - Adjustable status interval
  - Log level control
  - Optional API server
- **Better Error Handling**: Comprehensive exception handling and logging
- **Code Organization**: Clear separation of concerns and single responsibility

### Changed

#### Performance
- **Optimized Frame Processing**: Separated frame capture and processing threads
- **Smarter Detection**: Only run hand gesture detection when person is present
- **Efficient Image Conversion**: Use NumPy slicing instead of cv2.cvtColor
- **Buffered Presence Detection**: Smoothing using deque buffer to reduce false positives

#### Reliability
- **Graceful Degradation**: System continues with warnings if some capabilities fail
- **Better Resource Management**: Proper cleanup on shutdown
- **Thread Safety**: Locks for shared resource access
- **Error Recovery**: Automatic retry logic for transient failures

### Maintained

#### Backward Compatibility
- **Original Functionality**: All v1.x features fully preserved
- **Original Script**: main-mediapipe.py still available and functional
- **Deploy Script**: Original deploy.sh still works
- **No Breaking Changes**: Existing WOL.sh and configuration files work as-is

#### Core Features
- **MediaPipe Pose Detection**: Same detection algorithm and confidence thresholds
- **MediaPipe Hand Gesture**: Same victory gesture detection logic
- **GPIO Control**: Identical GPIO pin control behavior
- **Wake-on-LAN**: Same WOL trigger mechanism
- **Time-based Delays**: Same day/night delay logic

### Technical Details

#### Dependencies
- numpy>=1.19.0
- opencv-python>=4.5.0
- mediapipe>=0.10.0
- PyYAML>=5.4.0 (new)
- requests>=2.25.0 (optional, for API client)

#### File Structure
```
visiondetect/
├── core/              # Core orchestration and configuration
├── capabilities/      # Detection and control modules
├── utils/             # Utilities (logging, stats, API)
└── configs/           # Configuration files
```

#### Configuration
- All settings now in `visiondetect/configs/default.yaml`
- Supports custom config files via CLI
- Environment variable override support (planned)

#### API
- Built-in HTTP server using standard library
- JSON responses
- CORS support for web clients
- RESTful design

### Migration Guide

#### From v1.x to v2.0

1. **Backup your custom settings**
   - Save any modifications to main-mediapipe.py
   - Note your WOL.sh configuration

2. **Deploy v2.0**
   ```bash
   chmod +x deploy_v2.sh
   sudo ./deploy_v2.sh
   ```

3. **Update configuration**
   - Edit `visiondetect/configs/default.yaml`
   - Apply your custom settings

4. **Test**
   ```bash
   python scripts/health_check.py
   python main.py --status-interval 5
   ```

5. **Enable API (optional)**
   ```bash
   python main.py --enable-api --api-port 8080
   ```

#### Reverting to v1.x

If needed, you can always revert:
```bash
# Update systemd service to use old script
sudo systemctl edit visiondorm.service
# Change ExecStart to point to main-mediapipe.py
```

### Known Issues

- API server uses basic HTTP server (no HTTPS support yet)
- No authentication on API endpoints (planned for future release)
- Health check requires dependencies to be installed

### Future Plans

#### Planned for v2.1.0
- [ ] HTTPS support for API
- [ ] API authentication
- [ ] WebSocket support for real-time updates
- [ ] Multi-camera support
- [ ] Image capture and storage

#### Planned for v2.2.0
- [ ] Web dashboard
- [ ] Mobile app integration
- [ ] Email/Slack notifications
- [ ] Cloud integration
- [ ] Data analytics

#### Planned for v3.0.0
- [ ] Machine learning model training interface
- [ ] Custom gesture training
- [ ] Advanced scheduling
- [ ] Multi-room support

## [1.0.0] - 2025-01-01

### Initial Release
- MediaPipe pose detection
- Hand gesture recognition (V gesture)
- GPIO light control
- Wake-on-LAN trigger
- Day/night scheduling
- Basic FPS monitoring
- SystemD service integration

---

**Note**: v2.0 is fully backward compatible. All v1.x functionality is preserved.
