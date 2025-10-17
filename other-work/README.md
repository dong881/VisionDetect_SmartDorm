# Other Work - 詳細說明

本目錄包含了訓練模型和其他實驗性功能的相關檔案。這些工具用於收集資料、訓練模型以及測試模型效果。

## 目錄結構

```
other-work/
├── collect-data.py    # 收集姿勢和人臉資料
├── train-data.py      # 訓練模型
├── test-model.py      # 測試訓練好的模型
├── main.py            # 使用訓練模型進行偵測
├── WS2812.py          # WS2812 LED 燈控制
├── WOL.sh             # Wake-on-LAN 腳本
├── dong_model.h5      # 訓練好的模型檔案
└── data/              # 訓練資料目錄
```

## 詳細說明

### 1. collect-data.py - 資料收集工具

**功能描述：**
收集人體姿勢和人臉資料並儲存為 JSON 檔案。使用 MediaPipe 進行姿勢和人臉偵測，將關鍵點資料正規化後儲存。

**使用方法：**

1. 確保相機已連接
2. 執行腳本：
   ```bash
   cd other-work
   python3 collect-data.py
   ```

3. 操作說明：
   - 預設會收集「有人」的資料（`DEFAULT_TYPE = True`）
   - 按下 `t` 鍵切換資料類型（有人/無人）
   - 按下 `q` 鍵結束收集並儲存資料
   - 資料會儲存在 `data/` 目錄下，檔名包含時間戳記

**資料格式：**
- 每筆資料包含 7 個特徵值：
  - 姿勢關鍵點的平均 x, y, z 座標
  - 人臉偵測的信心度
  - 其他正規化特徵
- 標籤：`True` 表示有人，`False` 表示無人

**注意事項：**
- 建議在不同光線條件下收集資料
- 收集多種姿勢和角度的資料以提高模型準確度
- 至少需要收集 100+ 筆資料才能訓練出有效的模型

---

### 2. train-data.py - 模型訓練工具

**功能描述：**
使用收集的資料訓練一個神經網路模型，用於判斷是否有人出現在鏡頭前。

**使用方法：**

1. 確保已收集足夠的訓練資料（`data/` 目錄中的 JSON 檔案）
2. 執行訓練腳本：
   ```bash
   cd other-work
   python3 train-data.py
   ```

3. 訓練過程：
   - 自動載入 `data/` 目錄中的所有 JSON 資料
   - 資料會被分為訓練集和測試集（80%/20%）
   - 訓練 50 個 epoch（可根據需要調整）
   - 訓練完成後模型會儲存為 `dong_model.h5`

**模型架構：**
- 輸入層：7 個特徵
- 隱藏層：使用 ReLU 激活函數
- 輸出層：使用 Sigmoid 激活函數（二元分類）
- 優化器：Adam
- 損失函數：Binary Crossentropy

**訓練建議：**
- 確保訓練資料平衡（有人和無人的資料量接近）
- 監控訓練準確度和驗證準確度
- 如果過擬合，可以增加 dropout 或減少 epoch 數量

---

### 3. test-model.py - 模型測試工具

**功能描述：**
使用訓練好的模型進行即時測試，查看模型的預測效果。

**使用方法：**

1. 確保 `dong_model.h5` 模型檔案存在
2. 執行測試腳本：
   ```bash
   cd other-work
   python3 test-model.py
   ```

3. 測試過程：
   - 開啟相機即時預測
   - 螢幕上會顯示預測結果和信心度
   - 按 `q` 鍵結束測試

**評估指標：**
- 預測值：0-1 之間的浮點數
  - 接近 0：無人
  - 接近 1：有人
- 建議閾值：0.5（可根據實際需求調整）

---

### 4. main.py - 使用訓練模型進行偵測

**功能描述：**
在 Raspberry Pi 上使用訓練好的模型進行人體姿勢偵測，並控制 GPIO 輸出。

**使用方法：**

1. 確保已訓練好模型 `dong_model.h5`
2. 執行偵測腳本：
   ```bash
   cd other-work
   python3 main.py
   ```

**功能特點：**
- 使用訓練好的模型進行即時偵測
- 當偵測到人時，設定 GPIO 為 HIGH
- 當超過設定時間未偵測到人，設定 GPIO 為 LOW
- 可調整 `max_continuous_time` 參數（預設 5 秒）

**GPIO 設定：**
- GPIO pin：17（BCM 模式）
- 輸出模式：GPIO.OUT
- HIGH：有人偵測到
- LOW：無人偵測到

**注意事項：**
- 需要在 Raspberry Pi 上執行
- 確保 GPIO 權限設定正確
- 可能需要 root 權限執行

---

### 5. WS2812.py - LED 燈控制

**功能描述：**
控制 WS2812 LED 燈條的顏色和亮度。

**使用方法：**

```bash
cd other-work
python3 WS2812.py
```

**功能特點：**
- 支援 RGB 顏色控制
- 可調整亮度
- 支援燈效動畫

**硬體需求：**
- WS2812 LED 燈條
- 正確的電源供應
- 連接到指定的 GPIO pin

---

### 6. WOL.sh - Wake-on-LAN 腳本

**功能描述：**
發送 Wake-on-LAN 魔術封包喚醒目標電腦。

**使用方法：**

```bash
cd other-work
./WOL.sh
```

**設定說明：**
- 編輯腳本中的 MAC 位址
- 確保目標電腦支援 WOL 功能
- 目標電腦的 BIOS 需要啟用 WOL

---

## 完整使用流程

### 方法 1：使用訓練模型（需要訓練）

適用於想要客製化偵測邏輯的使用者。

**步驟 1：收集訓練資料**
```bash
cd other-work
python3 collect-data.py
```
- 在不同場景下收集有人和無人的資料
- 收集至少 200+ 筆資料（100 筆有人，100 筆無人）
- 資料會儲存在 `data/` 目錄

**步驟 2：訓練模型**
```bash
python3 train-data.py
```
- 自動載入收集的資料
- 訓練完成後產生 `dong_model.h5` 模型檔案
- 觀察訓練準確度，確保 > 90%

**步驟 3：測試模型**
```bash
python3 test-model.py
```
- 即時測試模型效果
- 根據測試結果調整訓練參數或重新收集資料

**步驟 4：部署使用**
```bash
python3 main.py
```
- 使用訓練好的模型進行即時偵測
- 控制 GPIO 輸出

### 方法 2：直接使用 MediaPipe（不需訓練）

推薦使用主目錄的 `main-mediapipe-judge.py`，無需訓練即可使用。

優點：
- 不需要收集資料和訓練
- 使用 Google 訓練好的 MediaPipe 模型
- 準確度高，效能好
- 支援更多進階功能（手勢辨識、分割等）

---

## 進階設定

### 在 Windows 上訓練模型

如果您想在 Windows 上進行資料收集和模型訓練，然後將模型部署到 Raspberry Pi：

**在 Windows 上：**

1. 安裝虛擬環境：
   ```bash
   virtualenv myenv
   cd myenv/Scripts
   activate
   ```

2. 安裝依賴套件：
   ```bash
   pip install mediapipe
   pip install tensorflow
   pip install opencv-python
   pip install numpy
   ```

3. 收集資料並訓練：
   ```bash
   cd other-work
   python collect-data.py
   python train-data.py
   ```

4. 將 `dong_model.h5` 傳輸到 Raspberry Pi

**在 Raspberry Pi 上：**

1. 安裝必要套件：
   ```bash
   pip install tensorflow
   pip install opencv-python
   pip install mediapipe
   pip install RPi.GPIO
   ```

2. 執行偵測：
   ```bash
   python3 main.py
   ```

---

## 疑難排解

### 問題 1：相機無法開啟
**解決方法：**
- 檢查相機連接
- 嘗試不同的相機索引（0, 1, 2...）
- 確認相機權限設定

### 問題 2：MediaPipe 安裝失敗
**解決方法：**
- 在 Raspberry Pi 上安裝時間較長（約 1 小時）
- 確保有足夠的記憶體和儲存空間
- DietPI 系統需要額外安裝編譯工具：
  ```bash
  sudo apt install build-essential python3-dev
  ```

### 問題 3：訓練準確度低
**解決方法：**
- 收集更多訓練資料
- 確保資料品質和多樣性
- 調整模型架構和參數
- 增加訓練 epoch 數量

### 問題 4：GPIO 權限錯誤
**解決方法：**
- 使用 sudo 執行：`sudo python3 main.py`
- 或將使用者加入 gpio 群組：
  ```bash
  sudo usermod -a -G gpio $USER
  ```

---

## 參考資源

- [MediaPipe 官方文件](https://google.github.io/mediapipe/)
- [TensorFlow/Keras 教學](https://www.tensorflow.org/tutorials)
- [Raspberry Pi GPIO 教學](https://www.raspberrypi.org/documentation/usage/gpio/)
- [OpenCV Python 教學](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)

---

## 授權

本專案採用 MIT License - 詳見主目錄的 [LICENSE](../LICENSE) 檔案。

## 貢獻

歡迎提交 Pull Request 或回報問題！

