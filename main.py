import RPi.GPIO as GPIO
import cv2
import threading
import time
import numpy as np
import mediapipe as mp
from tensorflow.keras.models import load_model
import multiprocessing

# for i in range(10):  # Try indices from 0 to 9
#     cap = cv2.VideoCapture(i)
#     if cap.isOpened():
#         print(f"Camera index {i}: {cap.get(cv2.CAP_PROP_FRAME_WIDTH)}x{cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}")
#         cap.release()


# Global variables
frame = None

# 初始化 GPIO
GPIO_PIN = 17  # 更改為你實際使用的 GPIO pin
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_PIN, GPIO.OUT)

# 初始化變數
max_continuous_time = 5  # 最大持續時間，單位為秒
person_near_camera = False
last_detection_time = 0  # 上一次偵測到人的時間

# 控制 GPIO 狀態
GPIO_STATE = False
GPIO_TARGET_STATE = False

# 載入訓練好的模型
# model = load_model('dong_model.h5')  # 記得換成你的模型檔名

# Lock 用於確保多執行緒安全訪問共享資源
lock = multiprocessing.Lock()

def read_frame(frame_queue):
    # 初始化 OpenCV 視訊捕捉
    cap = cv2.VideoCapture(0)  # 可根據需要更改視訊源
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_queue.put(frame)
    cap.release()

# Start reading frames using multiprocessing
frame_queue = multiprocessing.Queue()
read_process = multiprocessing.Process(target=read_frame, args=(frame_queue,))
read_process.start()

# def preprocess_and_reshape(frame):

#     mp_pose = mp.solutions.pose
#     mp_face = mp.solutions.face_detection

#     # 初始化mediapipe
#     pose = mp_pose.Pose()
#     face = mp_face.FaceDetection(min_detection_confidence=0.2)

#     # 轉換為RGB
#     rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

#     # 進行pose detection
#     results_pose = pose.process(rgb_frame)

#     # 進行face detection
#     results_face = face.process(rgb_frame)

#     # 提取關鍵點
#     pose_landmarks = results_pose.pose_landmarks.landmark if results_pose.pose_landmarks else None
#     face_landmarks = results_face.detections if results_face.detections else None

#     # 將資料正規化
#     if pose_landmarks is not None and len(pose_landmarks) > 0 and face_landmarks is not None and len(face_landmarks) > 0:
#         # 確保 pose_landmarks 和 face_landmarks 的維度一致
#         pose_landmarks = [[landmark.x, landmark.y, landmark.z] for landmark in pose_landmarks]
#         face_landmarks = [[detection.location_data.relative_bounding_box.xmin,
#                             detection.location_data.relative_bounding_box.ymin,
#                             detection.location_data.relative_bounding_box.width,
#                             detection.location_data.relative_bounding_box.height] for detection in face_landmarks]

#         # 調整維度一致
#         min_length = min(len(pose_landmarks), len(face_landmarks))
#         pose_landmarks = np.array(pose_landmarks)[:min_length]
#         face_landmarks = np.array(face_landmarks)[:min_length]

#         # 進行連接
#         concatenated_data = np.concatenate([pose_landmarks, face_landmarks], axis=1)

#         # 注意這裡，將資料的維度降為 (7,)，假設 concatenated_data 的形狀是 (1, 7)
#         concatenated_data = np.squeeze(concatenated_data)
#         return concatenated_data
#     else:
#         # 如果提取不到資料，返回全為零的陣列（或其他預設值）
#         return np.zeros((7,))

def preprocess_and_reshape(frame):
    pose_landmarks = get_pose_landmarks(frame)
    face_landmarks = get_face_landmarks(frame)
    
    if pose_landmarks and face_landmarks:
        pose_landmarks = normalize_landmarks(pose_landmarks)
        face_landmarks = normalize_landmarks(face_landmarks)
        
        landmarks = truncate_and_concat(pose_landmarks, face_landmarks)
        return landmarks[0] if landmarks.shape[0] == 1 else np.squeeze(landmarks)

    return np.zeros(7)

def get_pose_landmarks(frame):
    # EXISTING POSE LANDMARK EXTRACTION CODE
    return pose_landmarks or None

def get_face_landmarks(frame):   
    # EXISTING FACE LANDMARK EXTRACTION CODE
    return face_landmarks or None

def normalize_landmarks(landmarks):
    return [[lmk.x, lmk.y, lmk.z] for lmk in landmarks]

def truncate_and_concat(pose, face):
    min_len = min(len(pose), len(face))
    truncated_pose = pose[:min_len] 
    truncated_face = face[:min_len]
    return np.concatenate([truncated_pose, truncated_face], axis=1)


def process_frame(frame_queue):
    global preprocess_and_reshape, last_detection_time, GPIO_STATE, GPIO_TARGET_STATE
    if True:
        if not frame_queue.empty():
            frame = frame_queue.get()
            print(frame)

            with lock:
                print("process")
                # 判斷人是否靠近鏡頭
                input_data = preprocess_and_reshape(frame)
                print(input_data)
                # prediction = model.predict(np.expand_dims(input_data, axis=0))[0]
                # if prediction > 0.7:
                #     # 更新偵測到人的時間
                #     last_detection_time = time.time()
                #     GPIO_TARGET_STATE = True
                # else:
                #     # 如果持續時間超過設定的最大持續時間，則設定為 False
                #     if time.time() - last_detection_time > max_continuous_time:
                #         GPIO_TARGET_STATE = False

                # print(prediction)

                # 控制 GPIO 狀態漸進過渡
                if GPIO_STATE != GPIO_TARGET_STATE:
                    GPIO_STATE = GPIO_TARGET_STATE
                    if GPIO_STATE:
                        GPIO.output(GPIO_PIN, GPIO.HIGH)
                    else:
                        GPIO.output(GPIO_PIN, GPIO.LOW)

# Start processing frames using multiprocessing
process_process = multiprocessing.Process(target=process_frame, args=(frame_queue,))
process_process.start()

# 主執行緒繼續處理其他事務或等待
# ...

# 等待辨識執行完成
process_process.join()

# 等待讀取執行完成
read_process.join()

# 關閉視窗（如果有的話）
cv2.destroyAllWindows()

# 釋放 GPIO 資源
GPIO.cleanup()
