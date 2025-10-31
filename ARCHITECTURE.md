# VisionDetect SmartDorm v2.0 - Architecture Guide

本文檔說明 VisionDetect SmartDorm v2.0 的新架構設計。

## 架構概覽

v2.0 採用模組化設計，將系統分為清晰的層次：

```
visiondetect/
├── core/                    # 核心模組
│   ├── config.py           # 配置管理
│   ├── interfaces.py       # 能力接口定義
│   └── orchestrator.py     # 主協調器
├── capabilities/            # 能力模組
│   ├── camera.py           # 攝像頭捕獲
│   ├── pose_detection.py  # 人體姿態檢測
│   ├── hand_gesture.py    # 手勢識別
│   ├── light_control.py   # 燈光控制
│   └── wol.py             # Wake-on-LAN
├── utils/                  # 工具模組
│   ├── logger.py          # 日誌系統
│   └── statistics.py      # 統計追蹤
└── configs/               # 配置文件
    └── default.yaml       # 默認配置
```

## 主要改進

### 1. 模組化架構
- **關注點分離**：每個模組負責單一功能
- **可擴展性**：易於添加新功能
- **可測試性**：每個模組可獨立測試
- **可維護性**：清晰的代碼結構

### 2. 配置管理
- YAML 配置文件
- 支持環境變量覆蓋
- 集中化參數管理
- 熱重載支持

### 3. 增強的日誌系統
- 結構化日誌
- 分級日誌（DEBUG, INFO, WARNING, ERROR, CRITICAL）
- 日誌輪換
- 同時輸出到文件和控制台

### 4. 性能監控
- FPS 追蹤（捕獲和處理）
- 處理時間統計
- 檢測統計
- 系統健康指標

### 5. 統計追蹤
- 幀處理計數
- 人員檢測率
- 手勢識別次數
- WOL 觸發次數
- 燈光切換次數
- 錯誤計數

## 配置說明

配置文件位於 `visiondetect/configs/default.yaml`，主要配置項：

### 系統設置
```yaml
system:
  log_level: "INFO"      # 日誌級別
  log_dir: "LOG"         # 日誌目錄
```

### GPIO 配置
```yaml
gpio:
  pin: 18               # GPIO 引腳（BCM 模式）
  mode: "BCM"           # GPIO 模式
```

### 攝像頭設置
```yaml
camera:
  device_id: 0          # 攝像頭設備 ID
  width: 640            # 分辨率寬度
  height: 480           # 分辨率高度
  fps: 30               # 幀率
```

### 檢測參數
```yaml
pose_detection:
  min_detection_confidence: 0.6
  min_tracking_confidence: 0.6

hand_detection:
  min_detection_confidence: 0.75
  min_tracking_confidence: 0.6

presence:
  buffer_size: 5        # 平滑緩衝區大小
  threshold: 0.7        # 存在閾值
```

### 手勢設置
```yaml
gesture:
  hold_time: 1.5        # 手勢持續時間（秒）
  victory_confidence_threshold: 0.8
```

### 燈光控制
```yaml
light_control:
  day_start_hour: 8
  day_end_hour: 22
  off_delay:
    day: 300            # 白天延遲（秒）
    night: 180          # 夜間延遲（秒）
```

### Wake-on-LAN
```yaml
wol:
  cooldown: 90          # 冷卻時間（秒）
  script_path: "./WOL.sh"
```

## 使用方法

### 基本用法

```bash
# 使用默認配置
python main.py

# 使用自定義配置
python main.py --config /path/to/config.yaml

# 設置日誌級別
python main.py --log-level DEBUG

# 自定義狀態報告間隔
python main.py --status-interval 30
```

### 健康檢查

```bash
python scripts/health_check.py
```

健康檢查會驗證：
- Python 依賴項
- 攝像頭可訪問性
- GPIO 可用性
- 配置文件有效性

### 部署到 Raspberry Pi

使用新的部署腳本：

```bash
chmod +x deploy_v2.sh
sudo ./deploy_v2.sh
```

部署腳本會：
1. 安裝 Miniconda
2. 創建 Python 環境
3. 安裝依賴項
4. 運行健康檢查
5. 創建 systemd 服務
6. 啟動服務

## 向後兼容性

v2.0 完全保留了原有功能：
- 所有檢測邏輯保持不變
- GPIO 控制行為相同
- 手勢識別算法相同
- 原始的 `main-mediapipe.py` 仍然可用

部署腳本會自動選擇：
- 如果 `main.py` 存在，使用新架構
- 否則回退到 `main-mediapipe.py`

## API 使用示例

### 程式化使用

```python
from visiondetect.core.orchestrator import SmartDormOrchestrator

# 創建協調器
orchestrator = SmartDormOrchestrator()

# 初始化
if orchestrator.initialize_all():
    # 啟動系統
    orchestrator.start()
    
    try:
        while True:
            # 獲取狀態
            status = orchestrator.get_status()
            print(f"Person present: {status['person_present']}")
            print(f"Light state: {status['light_state']}")
            time.sleep(10)
    except KeyboardInterrupt:
        pass
    finally:
        # 停止並清理
        orchestrator.stop()
        orchestrator.cleanup_all()
```

### 自定義能力模組

```python
from visiondetect.core.interfaces import Detector

class MyCustomDetector(Detector):
    def initialize(self) -> bool:
        # 初始化邏輯
        return True
    
    def cleanup(self):
        # 清理邏輯
        pass
    
    def is_ready(self) -> bool:
        return True
    
    def detect(self, frame):
        # 檢測邏輯
        return {'result': 'detected'}

# 在協調器中使用
orchestrator = SmartDormOrchestrator()
orchestrator.my_detector = MyCustomDetector()
```

## 性能優化

v2.0 包含多項性能優化：

1. **線程化幀捕獲**：分離幀捕獲和處理
2. **智能處理**：只在需要時執行手勢檢測
3. **緩衝區平滑**：減少誤檢測
4. **高效的圖像轉換**：使用 NumPy 切片代替 cv2.cvtColor
5. **統計追蹤**：最小化性能開銷

## 監控和調試

### 日誌文件

```bash
# 查看主日誌
tail -f LOG/visiondorm_YYYYMMDD.log

# 查看錯誤日誌
tail -f LOG/visiondorm_error_YYYYMMDD.log

# 查看 systemd 日誌
sudo journalctl -u visiondorm.service -f
```

### 性能指標

系統會自動報告：
- 處理 FPS
- 平均處理時間
- 人員檢測率
- 手勢識別次數
- 錯誤率

## 故障排除

### 問題：攝像頭無法打開

```bash
# 列出可用設備
v4l2-ctl --list-devices

# 測試攝像頭
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'FAIL')"
```

### 問題：GPIO 權限錯誤

```bash
# 將用戶添加到 gpio 組
sudo usermod -a -G gpio $USER

# 重新登錄使更改生效
```

### 問題：性能問題

1. 降低攝像頭分辨率（在 config.yaml 中）
2. 增加狀態報告間隔
3. 禁用手勢識別（如果不需要）
4. 檢查 CPU 溫度和節流

## 擴展性

### 添加新的檢測能力

1. 在 `visiondetect/capabilities/` 中創建新模組
2. 實現 `Detector` 接口
3. 在協調器中集成
4. 更新配置文件

### 添加新的控制器

1. 在 `visiondetect/capabilities/` 中創建新模組
2. 實現 `Controller` 接口
3. 在協調器中集成
4. 更新配置文件

### 添加新的通知器

1. 在 `visiondetect/capabilities/` 中創建新模組
2. 實現 `Notifier` 接口
3. 在協調器中集成
4. 更新配置文件

## 遷移指南

從 v1.x 遷移到 v2.0：

1. **備份現有配置**：保存自定義設置
2. **運行 deploy_v2.sh**：自動設置新版本
3. **更新配置**：在 `visiondetect/configs/default.yaml` 中應用自定義設置
4. **測試**：運行健康檢查並驗證功能
5. **部署**：重啟服務

v1.x 的功能完全保留，無需修改 WOL 腳本或其他腳本。

## 未來改進

計劃的功能：
- [ ] Web API 接口（REST/WebSocket）
- [ ] 遠程配置
- [ ] 多攝像頭支持
- [ ] 圖像存儲和回放
- [ ] ML 模型微調
- [ ] 移動應用集成
- [ ] 通知系統（郵件、Slack 等）
- [ ] 數據分析和可視化

## 貢獻

歡迎貢獻！請遵循以下準則：

1. 保持模組化設計
2. 編寫清晰的文檔
3. 添加單元測試
4. 遵循現有代碼風格
5. 更新 CHANGELOG

## 授權

Ming Hone HSU © 2025.

## 支持

- GitHub Issues: 報告問題和請求功能
- 文檔: 查看完整文檔
- 社區: 加入討論

---

**注意**：v2.0 是向後兼容的。所有 v1.x 功能都保留，您可以隨時回退到原始的 `main-mediapipe.py`。
