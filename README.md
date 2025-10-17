# VisionDetect SmartDorm - 智慧鏡面人體偵測系統

本專案使用 MediaPipe 在 Raspberry Pi 上進行即時人體姿勢偵測，並透過 GPIO 控制智慧鏡面的顯示。系統採用進階的偵測演算法，支援手勢辨識和智能燈光控制。

## 主要功能

- 🎯 **即時人體偵測**：使用 MediaPipe 進行高精度姿勢偵測
- 👋 **手勢辨識**：支援勝利手勢 (V) 觸發 Wake-on-LAN
- 💡 **智能燈光控制**：根據時間和人員存在自動調整燈光
- 🔄 **自動重啟**：系統服務異常時自動恢復
- 📊 **性能監控**：即時顯示 FPS 和系統狀態

## 快速部署

### 方法一：自動部署（推薦）

1. **複製專案到 Raspberry Pi：**
   ```bash
   git clone https://github.com/dong881/VisionDetect_SmartDorm.git
   cd VisionDetect_SmartDorm
   ```

2. **執行自動部署腳本：**
   ```bash
   chmod +x deploy.sh
   sudo ./deploy.sh
   ```

   腳本會自動完成以下工作：
   - ✅ 在家目錄建立 `pienv` 虛擬環境
   - ✅ 安裝所有必要套件（RPi.GPIO, mediapipe, opencv-python, numpy）
   - ✅ 建立並啟用 systemd 服務
   - ✅ 設定開機自動啟動
   - ✅ 建立日誌目錄

3. **檢查服務狀態：**
   ```bash
   sudo systemctl status visiondorm.service
   ```

部署完成！系統現在會自動在背景執行。

### 方法二：手動安裝

如果您想要手動控制安裝過程：

1. **安裝系統依賴：**
   ```bash
   sudo apt update
   sudo apt install python3-venv python3-pip
   # DietPI 使用者需要額外安裝：
   sudo apt install build-essential python3-dev
   ```

2. **建立虛擬環境：**
   ```bash
   python3 -m venv ~/pienv
   source ~/pienv/bin/activate
   ```

3. **安裝 Python 套件：**
   ```bash
   pip install --upgrade pip
   pip install RPi.GPIO opencv-python mediapipe numpy
   ```
   注意：在 Raspberry Pi 上安裝 mediapipe 可能需要約 1 小時。

4. **手動執行程式：**
   ```bash
   source ~/pienv/bin/activate
   python3 main-mediapipe-judge.py
   ```

## 系統需求

### 硬體需求
- Raspberry Pi 3B+ 或更新版本（建議 4B）
- USB 攝影機或 Raspberry Pi Camera Module
- 至少 2GB RAM
- 8GB+ SD 卡

### 軟體需求
- Raspberry Pi OS 或 DietPI
- Python 3.7+
- 網路連線（用於安裝套件）

## 使用說明

### 服務管理指令

```bash
# 查看服務狀態
sudo systemctl status visiondorm.service

# 啟動服務
sudo systemctl start visiondorm.service

# 停止服務
sudo systemctl stop visiondorm.service

# 重新啟動服務
sudo systemctl restart visiondorm.service

# 停用開機自動啟動
sudo systemctl disable visiondorm.service

# 啟用開機自動啟動
sudo systemctl enable visiondorm.service
```

### 查看日誌

```bash
# 即時查看運行日誌
tail -f LOG/visiondorm.log

# 即時查看錯誤日誌
tail -f LOG/visiondormError.log

# 查看服務日誌
sudo journalctl -u visiondorm.service -f
```

## 設定參數

您可以在 `main-mediapipe-judge.py` 中調整以下參數：

### GPIO 設定
```python
GPIO_PIN = 18  # 控制鏡面顯示的 GPIO pin（BCM 模式）
```

### 偵測參數
```python
POSE_DETECTION_CONFIDENCE = 0.6    # 人體偵測信心度閾值
HAND_DETECTION_CONFIDENCE = 0.75   # 手勢偵測信心度閾值
```

### 燈光控制
```python
LIGHT_OFF_DELAY = {
    "day": 300,    # 白天無人 5 分鐘後關燈
    "night": 180   # 夜間無人 3 分鐘後關燈
}
```

### Wake-on-LAN
```python
WOL_COOLDOWN = 90  # WOL 冷卻時間（秒）
```

## 進階功能

### 手勢控制

系統支援勝利手勢 (✌️) 來觸發 Wake-on-LAN：
1. 對著鏡頭做出 V 字手勢
2. 維持手勢 1.5 秒
3. 系統會自動發送 WOL 封包喚醒目標電腦

手勢辨識使用進階演算法，考慮手指角度、3D 位置和持續時間，確保準確性。

### 智能時間管理

系統會根據時間自動調整行為：
- **白天 (08:00-22:00)**：較長的關燈延遲（5分鐘）
- **夜間 (22:00-08:00)**：較短的關燈延遲（3分鐘）

## 其他工具和實驗性功能

如需使用訓練自訂模型或其他實驗性功能，請參閱 [other-work/README.md](other-work/README.md)。

該目錄包含：
- 資料收集工具
- 模型訓練腳本
- 測試工具
- LED 燈控制
- 詳細的步驟說明

## 疑難排解

### 問題 1：服務無法啟動
```bash
# 檢查服務日誌
sudo journalctl -u visiondorm.service -n 50

# 檢查 Python 路徑和虛擬環境
ls -la ~/pienv/bin/python3
```

### 問題 2：攝影機無法開啟
```bash
# 測試攝影機
raspistill -o test.jpg  # 對於 Pi Camera
v4l2-ctl --list-devices  # 對於 USB 攝影機

# 檢查權限
sudo usermod -a -G video $USER
```

### 問題 3：GPIO 權限錯誤
```bash
# 將使用者加入 gpio 群組
sudo usermod -a -G gpio $USER

# 重新登入後生效
```

### 問題 4：套件安裝失敗
```bash
# 確保有足夠的空間
df -h

# 增加 swap 空間（對於 mediapipe 安裝）
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile  # 設定 CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

## 貢獻

歡迎提交 Pull Request 或回報問題！如有任何改進建議，請隨時提出。

## 授權

本專案採用 MIT License - 詳見 [LICENSE](LICENSE) 檔案。

## 相關連結

- [MediaPipe 官方文件](https://google.github.io/mediapipe/)
- [Raspberry Pi GPIO 說明](https://www.raspberrypi.org/documentation/usage/gpio/)
- [OpenCV Python 教學](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)



