import RPi.GPIO as GPIO
import mediapipe
import cv2
import threading
import time
from mediapipe.python.solutions import pose
from mediapipe.python.solutions import hands
import datetime
import os
import numpy as np
from collections import deque

# 初始化 GPIO (禁用警告)
GPIO.setwarnings(False)
GPIO_PIN = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_PIN, GPIO.OUT)

# 系統配置參數
class Config:
    # 人體檢測參數
    POSE_DETECTION_CONFIDENCE = 0.6  # 提高檢測信心度
    POSE_TRACKING_CONFIDENCE = 0.6
    
    # 手勢檢測參數
    HAND_DETECTION_CONFIDENCE = 0.75  # 提高檢測信心度
    HAND_TRACKING_CONFIDENCE = 0.6
    
    # 視頻捕獲參數
    FRAME_WIDTH = 640
    FRAME_HEIGHT = 480
    
    # 系統參數
    WOL_COOLDOWN = 90  # 增加WOL冷卻時間為90秒
    
    # 手勢辨識參數
    GESTURE_HOLD_TIME = 1.5  # 持續手勢的時間
    
    # 人體檢測參數
    PRESENCE_BUFFER_SIZE = 5  # 歷史檢測結果緩衝區大小
    PRESENCE_THRESHOLD = 0.7  # 70%的檢測結果為真時確認存在人
    
    # 燈光控制參數
    LIGHT_OFF_DELAY = {
        "day": 300,   # 白天沒人5分鐘後關燈
        "night": 180  # 夜間沒人3分鐘後關燈
    }

# 初始化 MediaPipe 人體檢測模型
mp_pose = pose.Pose(
    min_detection_confidence=Config.POSE_DETECTION_CONFIDENCE,
    min_tracking_confidence=Config.POSE_TRACKING_CONFIDENCE,
    enable_segmentation=True,  # 啟用分割以提高準確性
    static_image_mode=False
)

# 初始化 MediaPipe 手勢檢測
mp_hands = hands.Hands(
    max_num_hands=1,
    min_detection_confidence=Config.HAND_DETECTION_CONFIDENCE,
    min_tracking_confidence=Config.HAND_TRACKING_CONFIDENCE,
    static_image_mode=False
)

# 初始化 OpenCV 視訊捕捉
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, Config.FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.FRAME_HEIGHT)
cap.set(cv2.CAP_PROP_FPS, 30)  # 嘗試設置更高的FPS

# 初始化變數
person_near_camera = False
last_detection_time = 0
last_wol_time = 0
last_gesture_start_time = 0
frame_count = 0  # 用於統計FPS

# 控制 GPIO 狀態
GPIO_STATE = False
GPIO_TARGET_STATE = False

# 人體存在檢測歷史記錄
presence_history = deque(maxlen=Config.PRESENCE_BUFFER_SIZE)

# 手勢歷史紀錄與狀態
class GestureState:
    NONE = 0
    POSSIBLE = 1
    CONFIRMED = 2

current_gesture_state = GestureState.NONE
gesture_start_time = 0
gesture_confidence = 0

# Lock 用於確保多執行緒安全訪問共享資源
lock = threading.Lock()
frame_lock = threading.Lock()  # 專門用於幀訪問的鎖

def calculate_finger_angles(hand_landmarks):
    """
    計算手指彎曲角度
    返回每個手指的彎曲角度(弧度)
    """
    # 手指關節索引
    finger_bases = [1, 5, 9, 13, 17]  # 手掌到每個手指的連接點
    finger_pips = [2, 6, 10, 14, 18]  # 第一關節
    finger_dips = [3, 7, 11, 15, 19]  # 第二關節
    finger_tips = [4, 8, 12, 16, 20]  # 指尖
    
    angles = []
    
    for f in range(5):  # 對每個手指
        # 獲取關節點
        base = hand_landmarks.landmark[finger_bases[f]]
        pip = hand_landmarks.landmark[finger_pips[f]]
        dip = hand_landmarks.landmark[finger_dips[f]]
        tip = hand_landmarks.landmark[finger_tips[f]]
        
        # 計算向量
        v1 = np.array([pip.x - base.x, pip.y - base.y, pip.z - base.z])
        v2 = np.array([dip.x - pip.x, dip.y - pip.y, dip.z - pip.z])
        v3 = np.array([tip.x - dip.x, tip.y - dip.y, tip.z - dip.z])
        
        # 正規化向量
        v1 = v1 / np.linalg.norm(v1)
        v2 = v2 / np.linalg.norm(v2)
        v3 = v3 / np.linalg.norm(v3)
        
        # 計算關節角度(弧度)
        angle1 = np.arccos(np.clip(np.dot(v1, v2), -1.0, 1.0))
        angle2 = np.arccos(np.clip(np.dot(v2, v3), -1.0, 1.0))
        
        # 總彎曲角度
        total_bend = angle1 + angle2
        angles.append(total_bend)
        
    return angles

def is_victory_gesture(hand_landmarks):
    """
    高級勝利手勢檢測，基於角度和3D位置
    """
    if not hand_landmarks:
        return 0.0  # 無手勢，返回0信心度
    
    # 計算所有手指的彎曲角度
    angles = calculate_finger_angles(hand_landmarks)
    
    # 獲取關鍵點
    wrist = hand_landmarks.landmark[0]
    index_tip = hand_landmarks.landmark[8]  # 食指尖
    index_dip = hand_landmarks.landmark[7]  # 食指第二關節
    index_pip = hand_landmarks.landmark[6]  # 食指第一關節
    index_mcp = hand_landmarks.landmark[5]  # 食指掌指關節
    
    middle_tip = hand_landmarks.landmark[12]  # 中指尖
    middle_dip = hand_landmarks.landmark[11]  # 中指第二關節
    middle_pip = hand_landmarks.landmark[10]  # 中指第一關節
    middle_mcp = hand_landmarks.landmark[9]  # 中指掌指關節
    
    ring_tip = hand_landmarks.landmark[16]  # 無名指尖
    ring_mcp = hand_landmarks.landmark[13]  # 無名指掌指關節
    
    pinky_tip = hand_landmarks.landmark[20]  # 小指尖
    pinky_mcp = hand_landmarks.landmark[17]  # 小指掌指關節
    
    thumb_tip = hand_landmarks.landmark[4]  # 拇指尖
    
    # 檢查食指和中指是否伸直 (使用深度信息)
    # 如果指尖比關節更遠離相機，則表示伸直
    index_straight = (angles[1] < 0.7) and (index_tip.z < index_dip.z)
    middle_straight = (angles[2] < 0.7) and (middle_tip.z < middle_dip.z)
    
    # 檢查其他手指是否彎曲
    ring_bent = (angles[3] > 1.0) and (ring_tip.y > ring_mcp.y)
    pinky_bent = (angles[4] > 1.0) and (pinky_tip.y > pinky_mcp.y)
    
    # 確保拇指不在食指和中指之間
    thumb_away = ((thumb_tip.x < index_mcp.x) or  # 拇指在食指左側
                  (thumb_tip.x > middle_mcp.x))    # 拇指在中指右側
    
    # 計算食指和中指之間的角度
    v_index = np.array([index_tip.x - index_mcp.x, index_tip.y - index_mcp.y])
    v_middle = np.array([middle_tip.x - middle_mcp.x, middle_tip.y - middle_mcp.y])
    
    # 正規化向量
    v_index = v_index / np.linalg.norm(v_index)
    v_middle = v_middle / np.linalg.norm(v_middle)
    
    # 計算點積和角度 (弧度)
    angle_between = np.arccos(np.clip(np.dot(v_index, v_middle), -1.0, 1.0))
    
    # 轉換為度數
    angle_deg = np.degrees(angle_between)
    
    # V形手勢應該有一定角度 (20-60度)
    good_angle = 20 < angle_deg < 60
    
    # 檢查食指和中指是否接近同一高度
    similar_height = abs(index_tip.y - middle_tip.y) < 0.1
    
    # 計算總體信心度 (0-1之間)
    # 每個條件貢獻權重
    confidence = 0.0
    if index_straight: confidence += 0.2
    if middle_straight: confidence += 0.2
    if ring_bent and pinky_bent: confidence += 0.2
    if good_angle: confidence += 0.2
    if similar_height and thumb_away: confidence += 0.2
    
    return confidence

def is_person_present(pose_results, segmentation_threshold=0.5):
    """
    高級人體存在檢測，結合關鍵點和分割結果
    返回信心度 (0-1)
    """
    if not pose_results.pose_landmarks:
        return 0.0
    
    landmarks = pose_results.pose_landmarks.landmark
    
    # 檢查關鍵點有效性和可見度
    valid_landmarks = sum(1 for lm in landmarks if lm.visibility > 0.7)
    landmark_confidence = valid_landmarks / len(landmarks)
    
    # 檢查人體在畫面中的位置
    nose = landmarks[pose.PoseLandmark.NOSE]
    left_eye = landmarks[pose.PoseLandmark.LEFT_EYE]
    right_eye = landmarks[pose.PoseLandmark.RIGHT_EYE]
    left_shoulder = landmarks[pose.PoseLandmark.LEFT_SHOULDER]
    right_shoulder = landmarks[pose.PoseLandmark.RIGHT_SHOULDER]
    left_hip = landmarks[pose.PoseLandmark.LEFT_HIP]
    right_hip = landmarks[pose.PoseLandmark.RIGHT_HIP]
    
    # 檢查人體是否在畫面中心區域
    # 計算關鍵點的平均x位置
    key_points = [nose, left_eye, right_eye, left_shoulder, right_shoulder]
    avg_x = sum(pt.x for pt in key_points) / len(key_points)
    
    # 中心區域判定
    in_center = 0.3 < avg_x < 0.7
    
    # 檢查上半身是否可見 (肩膀可見)
    upper_body_visible = (left_shoulder.visibility > 0.7 and 
                          right_shoulder.visibility > 0.7)
    
    # 檢查是否足夠靠近 (根據肩膀間距判斷)
    shoulder_distance = ((left_shoulder.x - right_shoulder.x)**2 + 
                         (left_shoulder.y - right_shoulder.y)**2)**0.5
    
    is_close = shoulder_distance > 0.2  # 肩膀間距足夠大，表示靠近
    
    # 分割圖是否顯示大量人體 (如果可用)
    segmentation_score = 0.0
    if pose_results.segmentation_mask is not None:
        # 計算分割圖中人體像素的比例
        segmentation_mask = pose_results.segmentation_mask
        total_pixels = segmentation_mask.shape[0] * segmentation_mask.shape[1]
        human_pixels = np.sum(segmentation_mask > segmentation_threshold)
        segmentation_score = min(human_pixels / total_pixels / 0.3, 1.0)  # 正規化到0-1
    
    # 綜合評分
    position_score = (0.4 if in_center else 0.0) + (0.3 if is_close else 0.0)
    visibility_score = 0.3 if upper_body_visible else 0.0
    
    # 最終信心度
    final_confidence = (0.4 * landmark_confidence + 
                       0.3 * position_score + 
                       0.2 * visibility_score + 
                       0.1 * segmentation_score)
    
    return min(final_confidence, 1.0)  # 確保不超過1.0

def send_custom_wol():
    """
    執行本地 WOL 腳本喚醒目標電腦
    """
    try:
        # 記錄嘗試時間
        attempt_time = datetime.datetime.now()
        print(f"Attempting to execute WOL script at {attempt_time}")
        
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
    if current_time - last_wol_time < Config.WOL_COOLDOWN:
        remaining = int(Config.WOL_COOLDOWN - (current_time - last_wol_time))
        print(f"WOL cooldown active. {remaining} seconds remaining.")
        return False
    
    success = send_custom_wol()
    if success:
        last_wol_time = current_time
        print(f"WOL packet successfully sent at {datetime.datetime.now()}")
    return success

def is_day_time():
    """
    判斷當前是否為白天 (8:00-22:00)
    """
    current_hour = datetime.datetime.now().hour
    return 8 <= current_hour < 22

def get_max_continuous_time():
    """
    根據當前時間獲取最大連續時間
    """
    if is_day_time():
        return Config.LIGHT_OFF_DELAY["day"]
    else:
        return Config.LIGHT_OFF_DELAY["night"]

def read_frame():
    """
    持續讀取並更新框架的執行緒函數 - 盡可能高頻
    """
    global frame
    last_fps_print = time.time()
    frame_count = 0
    
    while cap.isOpened():
        ret, captured_frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            time.sleep(0.1)
            continue
        
        # 使用鎖確保線程安全
        with frame_lock:
            frame = captured_frame
        
        # 統計FPS
        frame_count += 1
        current_time = time.time()
        if current_time - last_fps_print >= 5:  # 每5秒印一次FPS
            fps = frame_count / (current_time - last_fps_print)
            print(f"Camera capture FPS: {fps:.1f}")
            frame_count = 0
            last_fps_print = current_time
    
    cap.release()

def process_hand_gesture(hand_results, current_time):
    """
    處理手勢識別結果並觸發相應動作
    返回是否檢測到有效手勢
    """
    global current_gesture_state, gesture_start_time, gesture_confidence
    
    # 檢測勝利手勢並觸發 WOL
    if hand_results.multi_hand_landmarks:
        # 取得手勢信心度 (0-1)
        confidence = is_victory_gesture(hand_results.multi_hand_landmarks[0])
        
        # 狀態機處理
        if confidence > 0.8:  # 高信心度
            if current_gesture_state == GestureState.NONE:
                # 新檢測到手勢
                current_gesture_state = GestureState.POSSIBLE
                gesture_start_time = current_time
                gesture_confidence = confidence
                print(f"Possible victory gesture detected with confidence: {confidence:.2f}")
            
            elif current_gesture_state == GestureState.POSSIBLE:
                # 手勢持續中
                gesture_confidence = max(gesture_confidence, confidence)  # 取最高信心度
                
                # 檢查是否達到所需持續時間
                if current_time - gesture_start_time >= Config.GESTURE_HOLD_TIME:
                    current_gesture_state = GestureState.CONFIRMED
                    print(f"Victory gesture confirmed with confidence: {gesture_confidence:.2f}")
                    threading.Thread(target=send_wol).start()
                    return True
        
        elif confidence > 0.5:  # 中等信心度
            # 更新信心度但不改變狀態
            if current_gesture_state == GestureState.POSSIBLE:
                gesture_confidence = 0.7 * gesture_confidence + 0.3 * confidence  # 平滑更新
        
        else:  # 低信心度
            # 重置狀態
            if current_gesture_state != GestureState.NONE:
                print("Gesture tracking lost")
                current_gesture_state = GestureState.NONE
                gesture_confidence = 0
    
    else:  # 沒有檢測到手
        if current_gesture_state != GestureState.NONE:
            print("No hand detected, resetting gesture state")
            current_gesture_state = GestureState.NONE
            gesture_confidence = 0
    
    return False

def update_light_control(pose_confidence, current_time):
    """
    根據人體檢測結果更新燈光控制狀態
    """
    global person_near_camera, last_detection_time, GPIO_TARGET_STATE
    
    # 使用歷史緩衝區來平滑決策
    presence_history.append(pose_confidence > 0.5)
    
    # 計算歷史檢測中有人的比例
    presence_ratio = sum(presence_history) / len(presence_history)
    
    # 決策邏輯
    with lock:
        if presence_ratio >= Config.PRESENCE_THRESHOLD:
            # 人存在的概率高
            last_detection_time = current_time
            person_near_camera = True
            if not GPIO_TARGET_STATE:
                print(f"Person detected with confidence {presence_ratio:.2f}, turning light ON")
            GPIO_TARGET_STATE = True
        else:
            # 可能沒有人
            person_near_camera = False
            # 檢查是否超過延遲時間
            max_time = get_max_continuous_time()
            if current_time - last_detection_time > max_time:
                if GPIO_TARGET_STATE:
                    print(f"No person detected for {max_time} seconds, turning light OFF")
                GPIO_TARGET_STATE = False

def process_frame():
    """
    處理影像框架並執行檢測邏輯 - 盡可能快速處理
    """
    global frame, person_near_camera, last_detection_time, GPIO_STATE, GPIO_TARGET_STATE
    
    # 性能監控變數
    process_count = 0
    last_fps_print = time.time()
    
    while True:
        local_frame = None
        
        # 安全地獲取當前幀
        with frame_lock:
            if 'frame' in globals() and frame is not None:
                local_frame = frame.copy()
        
        if local_frame is not None:
            try:
                # 轉換影像格式並進行處理
                frame_rgb = cv2.cvtColor(local_frame, cv2.COLOR_BGR2RGB)
                
                # 進行人體檢測
                pose_results = mp_pose.process(frame_rgb)
                
                # 計算人體存在信心度
                pose_confidence = is_person_present(pose_results)
                
                # 進行手勢檢測，僅在人體存在時執行以節省資源
                if pose_confidence > 0.5:  # 只有在確認有人時才檢測手勢
                    hand_results = mp_hands.process(frame_rgb)
                    # 處理手勢狀態
                    if hand_results and hand_results.multi_hand_landmarks:
                        process_hand_gesture(hand_results, time.time())
                
                # 更新燈光控制
                update_light_control(pose_confidence, time.time())
                
                # 實際控制 GPIO
                with lock:
                    if GPIO_STATE != GPIO_TARGET_STATE:
                        GPIO_STATE = GPIO_TARGET_STATE
                        GPIO.output(GPIO_PIN, GPIO.HIGH if GPIO_STATE else GPIO.LOW)
                        print(f"Light state changed to: {'ON' if GPIO_STATE else 'OFF'}")
                
                # 性能監控
                process_count += 1
                current_time = time.time()
                if current_time - last_fps_print >= 5:  # 每5秒印一次處理FPS
                    fps = process_count / (current_time - last_fps_print)
                    print(f"Frame processing FPS: {fps:.1f}")
                    process_count = 0
                    last_fps_print = current_time
                
            except Exception as e:
                print(f"Error in process_frame: {e}")
        else:
            # 如果沒有可用的幀，短暫休眠以避免CPU空轉
            time.sleep(0.01)

# 開始讀取視訊的執行緒
read_thread = threading.Thread(target=read_frame)
read_thread.daemon = True
read_thread.start()

# 開始辨識的執行緒
process_thread = threading.Thread(target=process_frame)
process_thread.daemon = True
process_thread.start()

try:
    # 主執行緒顯示系統狀態
    while True:
        time.sleep(5)
        max_time = get_max_continuous_time()
        if person_near_camera:
            print(f"Status: Person detected. Light: {'ON' if GPIO_STATE else 'OFF'}")
        else:
            remain = max_time - (time.time() - last_detection_time)
            if remain > 0:
                print(f"Status: No person detected. Light will turn off in {int(remain)} seconds.")
            else:
                print(f"Status: No person detected. Light: {'ON' if GPIO_STATE else 'OFF'}")
except KeyboardInterrupt:
    print("Program terminated by user")
finally:
    # 清理資源
    print("Cleaning up resources...")
    cv2.destroyAllWindows()
    GPIO.cleanup()
    mp_pose.close()
    mp_hands.close()
    if cap.isOpened():
        cap.release()
    print("Cleanup complete. Exiting...")
