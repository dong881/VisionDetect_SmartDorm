# Smart Mirror with Person Detection

This project uses MediaPipe on Windows for pose detection model training. The trained model is deployed on a Raspberry Pi to detect persons and control mirror display via GPIO pin signals.

## Key Features

- Trains custom pose detection model on Windows 
- Deploys model on Raspberry Pi to detect people  
- Controls GPIO pin high/low to turn mirror display on/off
- Easy integration with other smart mirror capabilities

## Getting Started

### Prerequisites

- Raspberry Pi
- Camera module or USB webcam
- GPIO pins setup
- Python 3
- OpenCV 
- MediaPipe
### Installation

**On Windows:**

1. [Install virtal env](https://simplelearn.tw/python-virtualenv/)
   ```
   virtualenv <YOUR-ENV-NAME>
   cd <YOUR-PATH-TO-ENV-DIRC>
   activate
   ```

2. [Install mediapipe and relate](https://ithelp.ithome.com.tw/articles/10297967)
   ```
   pip install mediapipe
   pip install tensorflow
   pip install opencv-python
   ```

**On Raspberry Pi:**  

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



