# Smart Mirror with Person Detection README

This project utilizes a Raspberry Pi, a camera, and GPIO pins to create a smart mirror that detects when a person is near the mirror and adjusts its display accordingly. The person detection is based on the usage of the MediaPipe Pose model for detecting human poses.

## Requirements

- Raspberry Pi with GPIO pins
- Camera (USB or Raspberry Pi Camera Module)
- Python 3
- OpenCV
- MediaPipe

## Installation

1. Clone the repository to your Raspberry Pi:

   ```bash
   git clone https://github.com/your-username/smart-mirror.git
   ```

2. Install the required Python libraries:

   ```bash
   pip install RPi.GPIO opencv-python mediapipe
   ```

3. Connect your camera to the Raspberry Pi and make sure the GPIO pins are properly set up.

## Usage

1. Run the main Python script:

   ```bash
   python smart_mirror.py
   ```

2. The script will start capturing video from the camera and detecting the presence of a person.

3. The GPIO pin state will be controlled based on whether a person is detected near the mirror.

## Customization

You can customize the behavior of the smart mirror by adjusting the following parameters in the script:

- `GPIO_PIN`: Set the GPIO pin number used to control the mirror display.
- `max_continuous_time`: Set the maximum continuous time without person detection before considering the person is no longer present.
- `cap = cv2.VideoCapture(0)`: Adjust the video source if using a different camera.

Feel free to modify the script to add additional features or integrate it with other smart mirror functionalities.

## Contributing

If you have any improvements or suggestions, feel free to create a pull request. Contributions are welcome!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
