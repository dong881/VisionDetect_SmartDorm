import RPi.GPIO as GPIO
import mediapipe
import cv2
import threading
import time
from mediapipe.python.solutions import pose
from mediapipe.python.solutions import hands
import datetime
import os

# 初始化 GPIO (禁用警告)
GPIO.setwarnings(False)
GPIO_PIN = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_PIN, GPIO.OUT)

# 初始化 MediaPipe 人體檢測模型
mp_pose = pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    enable_segmentation=False,
    static_image_mode=False
)

# 初始化 MediaPipe 手勢檢測
mp_hands = hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5,
    static_image_mode=False
)

# 初始化 OpenCV 視訊捕捉
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# 初始化變數
max_continuous_time = 5
person_near_camera = False
last_detection_time = 0
last_wol_time = 0
WOL_COOLDOWN = 30
GESTURE_HOLD_TIME = 2.0  # 新增：需要持續手勢的時間
last_gesture_start_time = 0  # 新增：開始做手勢的時間

# 控制 GPIO 狀態
GPIO_STATE = False
GPIO_TARGET_STATE = False

# Lock 用於確保多執行緒安全訪問共享資源
lock = threading.Lock()

def is_victory_gesture(hand_landmarks):
    """
    檢測是否為勝利手勢 (V手勢)
    要求：
    1. 食指和中指伸直
    2. 其他手指彎曲
    3. 食指和中指之間有一定角度
    """
    if not hand_landmarks:
        return False
    
    # 獲取關鍵點
    index_tip = hand_landmarks.landmark[8]  # 食指尖
    index_pip = hand_landmarks.landmark[6]  # 食指第二關節
    middle_tip = hand_landmarks.landmark[12]  # 中指尖
    middle_pip = hand_landmarks.landmark[10]  # 中指第二關節
    ring_tip = hand_landmarks.landmark[16]  # 無名指尖
    pinky_tip = hand_landmarks.landmark[20]  # 小指尖
    
    # 檢查食指和中指是否伸直
    index_straight = index_tip.y < index_pip.y
    middle_straight = middle_tip.y < middle_pip.y
    
    # 檢查其他手指是否彎曲
    others_bent = (ring_tip.y > middle_pip.y and 
                  pinky_tip.y > middle_pip.y)
    
    # 計算食指和中指之間的角度
    fingers_distance = ((index_tip.x - middle_tip.x) ** 2 + 
                       (index_tip.y - middle_tip.y) ** 2) ** 0.5
    
    # 確保手指之間有足夠的距離（避免手指併攏）
    min_distance = 0.04  # 調整此值以改變所需的手指間距
    
    return (index_straight and middle_straight and 
            others_bent and fingers_distance > min_distance)

def send_custom_wol():
    """
    執行本地 WOL 腳本喚醒目標電腦
    """
    try:
        # 執行本地腳本
        result = os.system('./WOL.sh')
        
        # 檢查腳本執行結果
        if result == 0:
            print(f"WOL script executed successfully at {datetime.datetime.now()}")
            return True
        else:
            print(f"WOL script failed with exit code: {result}")
            return False
            
    except Exception as e:
        print(f"Error executing WOL script: {e}")
        return False

def send_wol():
    """
    發送 Wake-on-LAN 魔術封包
    """
    global last_wol_time
    current_time = time.time()
    
    # 檢查冷卻時間
    if current_time - last_wol_time < WOL_COOLDOWN:
        return False
    
    success = send_custom_wol()
    if success:
        last_wol_time = current_time
        print(f"WOL packet successfully sent at {datetime.datetime.now()}")
    return success

def is_person_near_camera(results):
    """
    判斷人是否靠近鏡頭，鼻子位於畫面正下方中間，靠近則返回 True。
    """
    if not results.pose_landmarks:
        return False

    landmarks = results.pose_landmarks.landmark

    # 取得特定部位的座標
    nose_coords = (landmarks[pose.PoseLandmark.NOSE].x,
                   landmarks[pose.PoseLandmark.NOSE].y)

    # 判斷鼻子是否位於畫面正下方中間位置
    near_camera = 0.3 < nose_coords[0] < 0.7 and nose_coords[1] > 0.3

    return near_camera

def is_person_near_camera_or_waist(results):
    """
    判斷人是否靠近鏡頭或露出腰部
    """
    if not results.pose_landmarks:
        return False

    landmarks = results.pose_landmarks.landmark

    # 取得鼻子和腰部的座標
    nose_coords = (landmarks[pose.PoseLandmark.NOSE].x,
                   landmarks[pose.PoseLandmark.NOSE].y)
    left_hip_coords = (landmarks[pose.PoseLandmark.LEFT_HIP].x,
                       landmarks[pose.PoseLandmark.LEFT_HIP].y)
    right_hip_coords = (landmarks[pose.PoseLandmark.RIGHT_HIP].x,
                        landmarks[pose.PoseLandmark.RIGHT_HIP].y)

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

def read_frame():
    global frame
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # 調整影像對比度和亮度
        # frame = adjust_contrast_brightness(frame)

    cap.release()

# 開始讀取視訊的執行緒
read_thread = threading.Thread(target=read_frame)
read_thread.start()

def process_frame():
    global frame, person_near_camera, last_detection_time, GPIO_STATE, GPIO_TARGET_STATE
    global last_gesture_start_time
    
    while True:
        if 'frame' in globals():
            try:
                # 根據當前時間更新 max_continuous_time
                max_continuous_time = update_max_continuous_time()

                # 轉換影像格式並進行處理
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # 進行人體檢測
                results = mp_pose.process(frame_rgb)
                
                # 進行手勢檢測
                hand_results = mp_hands.process(frame_rgb)

                # 檢測勝利手勢並觸發 WOL
                current_time = time.time()
                if hand_results.multi_hand_landmarks:
                    for hand_landmarks in hand_results.multi_hand_landmarks:
                        if is_victory_gesture(hand_landmarks):
                            if last_gesture_start_time == 0:
                                last_gesture_start_time = current_time
                            elif current_time - last_gesture_start_time >= GESTURE_HOLD_TIME:
                                print("Victory gesture held for required duration")
                                threading.Thread(target=send_wol).start()
                                last_gesture_start_time = 0  # 重置計時器
                        else:
                            last_gesture_start_time = 0  # 如果手勢中斷，重置計時器
                else:
                    last_gesture_start_time = 0  # 沒有檢測到手，重置計時器

                with lock:
                    # 判斷人是否靠近鏡頭或腰部
                    if is_person_near_camera_or_waist(results):
                        last_detection_time = current_time
                        person_near_camera = True
                        GPIO_TARGET_STATE = True
                    else:
                        person_near_camera = False
                        if current_time - last_detection_time > max_continuous_time:
                            GPIO_TARGET_STATE = False
                    
                    print(person_near_camera)
                    # 控制 GPIO 狀態漸進過渡
                    if GPIO_STATE != GPIO_TARGET_STATE:
                        GPIO_STATE = GPIO_TARGET_STATE
                        GPIO.output(GPIO_PIN, GPIO.HIGH if GPIO_STATE else GPIO.LOW)
            
            except Exception as e:
                print(f"Error in process_frame: {e}")
                time.sleep(0.1)

# 開始辨識的執行緒
process_thread = threading.Thread(target=process_frame)
process_thread.start()

try:
    # 主執行緒等待
    process_thread.join()
    read_thread.join()
finally:
    # 清理資源
    cv2.destroyAllWindows()
    GPIO.cleanup()
    mp_pose.close()
    mp_hands.close()
    cap.release()