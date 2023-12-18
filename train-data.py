import tensorflow as tf
from tensorflow import keras
from sklearn.model_selection import train_test_split
import json
import numpy as np
import os

# 讀取資料夾內的所有json檔案
data_path = "data"
all_data = []

for filename in os.listdir(data_path):
    if filename.endswith(".json"):
        file_path = os.path.join(data_path, filename)
        with open(file_path, "r") as f:
            data = json.load(f)
            all_data.extend(data)

# 提取特徵和標籤
X_data = []
y_data = []

for entry in all_data:
    if "concatenated_data" in entry:
        X_data.append(entry["concatenated_data"])
        y_data.append(entry["label"])

X = np.array(X_data)
y = np.array(y_data)

# 切割訓練集和測試集
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 建立模型
model = keras.Sequential([
    keras.layers.Dense(64, activation='relu', input_shape=(7,)),  # 這裡修改 input_shape
    keras.layers.Dense(32, activation='relu'),
    keras.layers.Dense(1, activation='sigmoid')
])


# 編譯模型
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# 訓練模型
model.fit(X_train, y_train, epochs=10, batch_size=32, validation_data=(X_test, y_test))

# 儲存模型
model.save('dong_model.h5')  # 你可以將 'your_model.h5' 換成你想要的模型檔名

# 評估模型
test_loss, test_acc = model.evaluate(X_test, y_test)
print(f'Test accuracy: {test_acc}')
