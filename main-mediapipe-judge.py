import RPi.GPIO as GPIO
import mediapipe
import cv2
import threading
import time
from mediapipe.python.solutions import pose as mp_pose
import datetime

# 初始化 GPIO
GPIO_PIN = 18  # 更改為你實際使用的 GPIO pin
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_PIN, GPIO.OUT)

# 初始化 MediaPipe 人體檢測模型
mp_pose_module = mediapipe.solutions.pose
mp_pose = mp_pose_module.Pose()

# 初始化 OpenCV 視訊捕捉
cap = cv2.VideoCapture(0)  # 可根據需要更改視訊源

# 初始化變數
max_continuous_time = 5  # 最大持續時間，單位為秒
person_near_camera = False
last_detection_time = 0  # 上一次偵測到人的時間

# 控制 GPIO 狀態
GPIO_STATE = False
GPIO_TARGET_STATE = False

# Lock 用於確保多執行緒安全訪問共享資源
lock = threading.Lock()

def read_frame():
    global frame
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

    # 釋放資源
    cap.release()

# 開始讀取視訊的執行緒
read_thread = threading.Thread(target=read_frame)
read_thread.start()

def is_person_near_camera(results):
    """
    判斷人是否靠近鏡頭，鼻子位於畫面正下方中間，靠近則返回 True。

    Parameters:
        results: MediaPipe 人體檢測的結果

    Returns:
        near_camera: True 表示人靠近鏡頭，False 表示人遠離鏡頭
    """
    # 如果偵測不到人，直接返回 False
    if not results.pose_landmarks:
        return False

    # 獲取骨架關鍵點
    landmarks = results.pose_landmarks.landmark

    # 取得特定部位的座標
    nose_coords = (landmarks[mp_pose_module.PoseLandmark.NOSE].x,
                   landmarks[mp_pose_module.PoseLandmark.NOSE].y)

    # 判斷鼻子是否位於畫面正下方中間位置
    near_camera = 0.3 < nose_coords[0] < 0.7 and nose_coords[1] > 0.3

    return near_camera

def is_person_near_camera_or_waist(results):
    """
    判斷人是否靠近鏡頭或露出腰部
    """
    # 如果偵測不到人，直接返回 False
    if not results.pose_landmarks:
        return False

    landmarks = results.pose_landmarks.landmark

    # 取得鼻子和腰部的座標
    nose_coords = (landmarks[mp_pose_module.PoseLandmark.NOSE].x,
                   landmarks[mp_pose_module.PoseLandmark.NOSE].y)
    left_hip_coords = (landmarks[mp_pose_module.PoseLandmark.LEFT_HIP].x,
                       landmarks[mp_pose_module.PoseLandmark.LEFT_HIP].y)
    right_hip_coords = (landmarks[mp_pose_module.PoseLandmark.RIGHT_HIP].x,
                        landmarks[mp_pose_module.PoseLandmark.RIGHT_HIP].y)

    # 判斷是否靠近（鼻子）或露出腰部
    near_camera = (0.3 < nose_coords[0] < 0.7 and nose_coords[1] > 0.3) or \
                  (0.3 < left_hip_coords[0] < 0.7 and left_hip_coords[1] > 0.5) or \
                  (0.3 < right_hip_coords[0] < 0.7 and right_hip_coords[1] > 0.5)

    return near_camera

def adjust_contrast_brightness(image, contrast=1.5, brightness=50):
    """
    調整影像對比度和亮度
    :param image: 影像
    :param contrast: 對比度
    :param brightness: 亮度
    :return: 調整後的影像
    """
    return cv2.convertScaleAbs(image, alpha=contrast, beta=brightness)

def update_max_continuous_time():
    """
    根據當前時間更新 max_continuous_time
    """
    current_hour = datetime.datetime.now().hour
    if 0 <= current_hour < 8:
        return 180
    else:
        return 300

def process_frame():
    global frame, person_near_camera, last_detection_time, GPIO_STATE, GPIO_TARGET_STATE
    while True:
        if 'frame' in globals():
            # 根據當前時間更新 max_continuous_time
            max_continuous_time = update_max_continuous_time()

            # 進行人體檢測
            results = mp_pose.process(frame)

            with lock:
                # 判斷人是否靠近鏡頭或腰部
                if is_person_near_camera_or_waist(results):
                    # 更新偵測到人的時間
                    last_detection_time = time.time()
                    person_near_camera = True
                    GPIO_TARGET_STATE = True
                else:
                    # 如果持續時間超過設定的最大持續時間，則設定為 False
                    person_near_camera = False
                    if time.time() - last_detection_time > max_continuous_time:
                        GPIO_TARGET_STATE = False
                print(person_near_camera)
                # 控制 GPIO 狀態漸進過渡
                if GPIO_STATE != GPIO_TARGET_STATE:
                    GPIO_STATE = GPIO_TARGET_STATE
                    GPIO.output(GPIO_PIN, GPIO.HIGH if GPIO_STATE else GPIO.LOW)

# 開始辨識的執行緒
process_thread = threading.Thread(target=process_frame)
process_thread.start()

# 主執行緒繼續處理其他事務或等待
# ...

# 等待辨識執行緒完成
process_thread.join()

# 等待讀取執行緒完成
read_thread.join()

# 關閉視窗（如果有的話）
cv2.destroyAllWindows()

# 釋放 GPIO 資源
GPIO.cleanup()
