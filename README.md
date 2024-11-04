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
   sudo apt install python3-venv
   python3 -m venv myenv
   source myenv/bin/activate
   sudo apt update
      #If you use DietPI OS
      sudo apt install build-essential python3-dev
      sudo apt install gcc-aarch64-linux-gn
      # about 1 hour
   pip install RPi.GPIO opencv-python mediapipe
   ```

3. Connect your camera to the Raspberry Pi and make sure the GPIO pins are properly set up.



## Usage

- Try running the main Python script:

   ```bash
   source myenv/bin/activate
   python3 smart_mirror.py
   ```
- The script will start capturing video from the camera and detecting the presence of a person.
- The GPIO pin state will be controlled based on whether a person is detected near the mirror.

## Running as a Service

To ensure that the person detection script runs automatically on startup and keeps running in the background, you can set it up as a systemd service on your Raspberry Pi.

### Setting up the Service

1. Create a new service file:

   ```bash
   sudo nano /etc/systemd/system/visiondorm.service
   ```

2. Add the following content to the service file:

   ```bash
   [Unit]
   Description=VisionDetect SmartDorm Service
   After=network.target

   [Service]
   WorkingDirectory=/root/VisionDetect_SmartDorm
   ExecStart=/bin/bash -c "source /root/VisionDetect_SmartDorm/dorm/bin/activate && python3 /root/VisionDetect_SmartDorm/main-mediapipe-judge.py"
   Restart=on-failure
   RestartSec=5
   StandardOutput=append:/root/VisionDetect_SmartDorm/LOG/visiondorm.log
   StandardError=append:/root/VisionDetect_SmartDorm/LOG/visiondormError.log

   [Install]
   WantedBy=multi-user.target
   ```

3. Reload the systemd manager configuration:

   ```bash
   sudo systemctl daemon-reload
   ```

4. Enable the service to start on boot:

   ```bash
   sudo systemctl enable visiondorm.service
   ```

5. Start the service:

   ```bash
   sudo systemctl start visiondorm.service
   ```

6. Check the status of the service:

   ```bash
   sudo systemctl status visiondorm.service
   ```

By following these steps, the person detection script will run automatically in the background, ensuring continuous operation of the smart mirror functionality.

### Other

## collect-data.py

收集姿勢和人臉資料並儲存為 JSON 檔。

```bash
python collect-data.py 
```

## train-model.py

訓練以收集的資料集建立的模型。

```bash  
python train-model.py
```

## main.py

在 Raspberry Pi 上使用訓練好的模型進行人體姿勢偵測。

```bash
python main.py
```

## mediapipe-main.py

利用 MediaPipe 直接進行偵測(無需訓練)。

```bash
python mediapipe-main.py  
```

## 其他檔案

data/*.json - 收集的訓練資料集 

dong_model.h5 - 訓練好的模型

## 使用流程

1. 收集資料(collect-data.py)  
2. 訓練模型(train-model.py) 
3. 啟動偵測(main.py)


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



