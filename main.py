import mediapipe
import cv2

# 初始化MediaPipe人體檢測模型
mp_holistic = mediapipe.solutions.holistic.Holistic()

# 初始化OpenCV視訊捕捉
cap = cv2.VideoCapture(0)  # 可根據需要更改視訊源

# 初始化變數
person_in_frame = False
frame_count = 0
threshold = 30  # 調整需要的連續幀數

while cap.isOpened():
    # 讀取一幀
    ret, frame = cap.read()
    if not ret:
        break

    # 轉換BGR圖片為RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # 進行人體檢測
    results = mp_holistic.process(rgb_frame)

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

    # 顯示畫面
    cv2.imshow('Frame', frame)

    # 按 'q' 鍵退出迴圈
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 釋放資源
cap.release()
cv2.destroyAllWindows()
