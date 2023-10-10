import mediapipe
import cv2
import threading

# 初始化MediaPipe人體檢測模型
mp_holistic = mediapipe.solutions.holistic.Holistic()

# 初始化OpenCV視訊捕捉
cap = cv2.VideoCapture(0)  # 可根據需要更改視訊源

# 初始化變數
person_in_frame = False
frame_count = 0
threshold = 30  # 調整需要的連續幀數

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
                        print("有人進入畫面！")
                        person_in_frame = True
                        frame_count = 0
                    else:
                        frame_count += 1
                        if frame_count >= threshold:
                            print("有人持續在畫面中！")
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
