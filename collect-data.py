import cv2
import mediapipe as mp
import numpy as np
import os
import json
from datetime import datetime

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
mp_face = mp.solutions.face_detection

# 初始化mediapipe
pose = mp_pose.Pose()
face = mp_face.FaceDetection(min_detection_confidence=0.2)

# 設定相機
cap = cv2.VideoCapture(1)

# 資料儲存路徑
data_path = "data"
os.makedirs(data_path, exist_ok=True)

# 資料收集
def collect_data():
    all_data = []
    is_true = False

    while True:
        ret, frame = cap.read()

        if not ret:
            break

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

            normalized_data = {
                # "timestamp": str(datetime.now()),
                "concatenated_data": concatenated_data.tolist(), 
                "label": 1 if is_true else 0
            }

            all_data.append(normalized_data)


        # 顯示影像
        annotated_frame = frame.copy()
        face_landmarks = results_face.detections if results_face.detections else None

        if face_landmarks is not None and len(face_landmarks) > 0:
            for detection in face_landmarks:
                bboxC = detection.location_data.relative_bounding_box  
                ih, iw, _ = frame.shape
                x, y, w, h = int(bboxC.xmin * iw), int(bboxC.ymin * ih), int(bboxC.width * iw), int(bboxC.height * ih)
                cv2.rectangle(annotated_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.imshow('Collecting Data', annotated_frame)

        # 按下空白鍵設為True，放開設為False
        key = cv2.waitKey(1) & 0xFF
        if key == ord(' '):
            is_true = True
        elif key == ord('q'):
            break
        elif key == 255:  # 空白鍵放開
            is_true = False

    cap.release()
    cv2.destroyAllWindows()

    # 儲存為json
    json_path = os.path.join(data_path, f"data_{datetime.now().strftime('%Y%m%d%H%M%S')}.json")
    with open(json_path, "w") as f:
        json.dump(all_data, f)

# 開始收集資料
collect_data()
