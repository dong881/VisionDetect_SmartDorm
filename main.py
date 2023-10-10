import mediapipe
import cv2
import threading
from mediapipe.python.solutions import pose as mp_pose


# 初始化MediaPipe人體檢測模型
mp_holistic = mediapipe.solutions.holistic.Holistic()

# 初始化OpenCV視訊捕捉
cap = cv2.VideoCapture(0)  # 可根據需要更改視訊源

# 初始化變數
person_in_frame = False
frame_count = 0
threshold = 5  # 調整需要的連續幀數

# Lock 用於確保多執行緒安全訪問共享資源
lock = threading.Lock()

def read_frame():
    global frame
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # 不顯示畫面

    # 釋放資源
    cap.release()

# 開始讀取視訊的執行緒
read_thread = threading.Thread(target=read_frame)
read_thread.start()

def is_person_seated_and_close(results, max_distance=100, seated_pose_threshold=0.5):
    """
    判斷人是否坐在椅子上，並且人的距離是否在一定範圍內。

    Parameters:
        results: MediaPipe 人體檢測的結果
        max_distance: 允許的最大距離，單位為像素
        seated_pose_threshold: 坐姿的置信度閾值，範圍在 0 到 1 之間

    Returns:
        seated: True 表示人坐在椅子上，False 表示人站著或者距離太遠
    """
    # 如果偵測不到人，直接返回 False
    if not results.pose_landmarks:
        return False

    # 獲取骨架關鍵點
    landmarks = results.pose_landmarks.landmark

    # 取得特定部位的座標
    nose_coords = (landmarks[mp_pose.PoseLandmark.NOSE].x,  
                landmarks[mp_pose.PoseLandmark.NOSE].y)

    left_hip_coords = (landmarks[mp_pose.PoseLandmark.LEFT_HIP].x,
                    landmarks[mp_pose.PoseLandmark.LEFT_HIP].y)

    right_hip_coords = (landmarks[mp_pose.PoseLandmark.RIGHT_HIP].x,
                        landmarks[mp_pose.PoseLandmark.RIGHT_HIP].y)
    # 計算鼻子和兩個髖關節的距離
    nose_to_left_hip_distance = ((nose_coords[0] - left_hip_coords[0]) ** 2 + (nose_coords[1] - left_hip_coords[1]) ** 2) ** 0.5
    nose_to_right_hip_distance = ((nose_coords[0] - right_hip_coords[0]) ** 2 + (nose_coords[1] - right_hip_coords[1]) ** 2) ** 0.5

    # 計算兩髖關節之間的距離，用於判斷是否坐在椅子上
    hip_distance = ((left_hip_coords[0] - right_hip_coords[0]) ** 2 + (left_hip_coords[1] - right_hip_coords[1]) ** 2) ** 0.5

    # 判斷坐姿的置信度是否足夠高
    seated_pose_confidence = results.pose_landmarks.landmark[0].z # 假設坐姿的 z 坐標較高

    # 判斷是否坐在椅子上且距離在範圍內
    seated = hip_distance < seated_pose_threshold and seated_pose_confidence > 0.5 \
             and nose_to_left_hip_distance < max_distance and nose_to_right_hip_distance < max_distance

    return seated



def process_frame():
    global frame, person_in_frame, frame_count
    while True:
        if 'frame' in globals():
            # 轉換BGR圖片為RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # 進行人體檢測
            results = mp_holistic.process(rgb_frame)

            with lock:  
                # 檢查是否有偵測到人
                if results.pose_landmarks:
                    if not person_in_frame:
                        print("有人進入畫面！"+ str(is_person_seated_and_close(results)))
                        person_in_frame = True
                        frame_count = 0
                    else:
                        frame_count += 1
                        if frame_count >= threshold:
                            print("有人持續在畫面中！"+ str(is_person_seated_and_close(results)))
                else:
                    if person_in_frame:
                        print("有人離開畫面！")
                        person_in_frame = False
                        frame_count = 0

                # 在畫面上繪製結果（可選）
                # ... （根據需要進行繪製）

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
