import cv2
import numpy as np
import mediapipe as mp
from tensorflow.keras.models import load_model

# 載入訓練好的模型
model = load_model('dong_model.h5')  # 記得換成你的模型檔名

# 開啟相機
cap = cv2.VideoCapture(1)  # 0 代表預設相機

def preprocess_and_reshape(frame):

    mp_pose = mp.solutions.pose
    mp_face = mp.solutions.face_detection

    # 初始化mediapipe
    pose = mp_pose.Pose()
    face = mp_face.FaceDetection(min_detection_confidence=0.2)

    # 轉換為RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # 進行pose detection
    results_pose = pose.process(rgb_frame)

    # 進行face detection
    results_face = face.process(rgb_frame)

    # 提取關鍵點
    pose_landmarks = results_pose.pose_landmarks.landmark if results_pose.pose_landmarks else None
    face_landmarks = results_face.detections if results_face.detections else None

    # 將資料正規化並加上時間戳
    if pose_landmarks is not None and len(pose_landmarks) > 0 and face_landmarks is not None and len(face_landmarks) > 0:
        # 確保 pose_landmarks 和 face_landmarks 的維度一致
        pose_landmarks = [[landmark.x, landmark.y, landmark.z] for landmark in pose_landmarks]
        face_landmarks = [[detection.location_data.relative_bounding_box.xmin,
                            detection.location_data.relative_bounding_box.ymin,
                            detection.location_data.relative_bounding_box.width,
                            detection.location_data.relative_bounding_box.height] for detection in face_landmarks]

        # 調整維度一致
        min_length = min(len(pose_landmarks), len(face_landmarks))
        pose_landmarks = np.array(pose_landmarks)[:min_length]
        face_landmarks = np.array(face_landmarks)[:min_length]

        # 進行連接
        concatenated_data = np.concatenate([pose_landmarks, face_landmarks], axis=1)

        # 注意這裡，將資料的維度降為 (7,)，假設 concatenated_data 的形狀是 (1, 7)
        concatenated_data = np.squeeze(concatenated_data)
        return concatenated_data
    else:
        # 如果提取不到資料，返回全為零的陣列（或其他預設值）
        return np.zeros((7,))

while True:
    # 讀取相機畫面
    ret, frame = cap.read()

    # 在這裡對 frame 進行預處理，確保與模型的 input_shape 相符

    # 進行模型預測
    input_data = preprocess_and_reshape(frame)
    prediction = model.predict(np.expand_dims(input_data, axis=0))[0]

    # 顯示結果
    label = "Positive" if prediction > 0.7 else "Negative"
    cv2.putText(frame, f"Prediction: {label}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # 顯示相機畫面
    cv2.imshow('Camera', frame)

    # 按 'q' 退出迴圈
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 釋放相機資源
cap.release()
cv2.destroyAllWindows()
