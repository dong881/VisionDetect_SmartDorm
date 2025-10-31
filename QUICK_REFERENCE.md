# Quick Reference Guide

快速參考指南 - VisionDetect SmartDorm v2.0

## 常用命令

### 基本操作

```bash
# 啟動系統
python main.py

# 啟動帶 API
python main.py --enable-api --api-port 8080

# 調試模式
python main.py --log-level DEBUG

# 健康檢查
python scripts/health_check.py

# API 示例
python scripts/api_example.py monitor
```

### 服務管理

```bash
# 查看狀態
sudo systemctl status visiondorm.service

# 啟動/停止/重啟
sudo systemctl start visiondorm.service
sudo systemctl stop visiondorm.service
sudo systemctl restart visiondorm.service

# 啟用/禁用開機自動啟動
sudo systemctl enable visiondorm.service
sudo systemctl disable visiondorm.service
```

### 日誌查看

```bash
# 主日誌（按日期）
tail -f LOG/visiondorm_$(date +%Y%m%d).log

# 錯誤日誌
tail -f LOG/visiondorm_error_$(date +%Y%m%d).log

# SystemD 日誌
sudo journalctl -u visiondorm.service -f

# 只看最近 50 行
sudo journalctl -u visiondorm.service -n 50
```

## API 端點

### GET 請求

```bash
# 系統狀態
curl http://localhost:8080/api/status

# 統計數據
curl http://localhost:8080/api/statistics

# 健康檢查
curl http://localhost:8080/api/health

# 燈光狀態
curl http://localhost:8080/api/light

# API 信息
curl http://localhost:8080/api
```

### POST 請求

```bash
# 開燈
curl -X POST http://localhost:8080/api/light \
  -H "Content-Type: application/json" \
  -d '{"state": true}'

# 關燈
curl -X POST http://localhost:8080/api/light \
  -H "Content-Type: application/json" \
  -d '{"state": false}'

# 觸發 WOL
curl -X POST http://localhost:8080/api/wol
```

## 配置

### 主要配置文件

`visiondetect/configs/default.yaml`

### 常用配置項

```yaml
# GPIO 設置
gpio:
  pin: 18

# 攝像頭設置
camera:
  device_id: 0
  width: 640
  height: 480

# 檢測信心度
pose_detection:
  min_detection_confidence: 0.6
hand_detection:
  min_detection_confidence: 0.75

# 燈光延遲
light_control:
  off_delay:
    day: 300    # 5 分鐘
    night: 180  # 3 分鐘

# WOL 冷卻時間
wol:
  cooldown: 90  # 90 秒
```

### 應用配置修改

```bash
# 1. 編輯配置
nano visiondetect/configs/default.yaml

# 2. 重啟服務
sudo systemctl restart visiondorm.service
```

## 故障排除

### 檢查清單

```bash
# 1. 系統健康檢查
python scripts/health_check.py

# 2. 查看服務狀態
sudo systemctl status visiondorm.service

# 3. 查看最近錯誤
sudo journalctl -u visiondorm.service -n 100 --no-pager | grep -i error

# 4. 測試攝像頭
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'FAIL')"

# 5. 檢查 GPIO 權限
groups | grep gpio
```

### 常見問題

#### 服務無法啟動

```bash
# 查看詳細日誌
sudo journalctl -u visiondorm.service -xe

# 檢查 Python 路徑
which python3

# 手動運行測試
cd /path/to/VisionDetect_SmartDorm
python main.py
```

#### 攝像頭錯誤

```bash
# 列出設備
v4l2-ctl --list-devices

# 測試不同設備 ID
python -c "import cv2; cap = cv2.VideoCapture(1); print(cap.isOpened())"

# 檢查權限
sudo usermod -a -G video $USER
```

#### GPIO 權限錯誤

```bash
# 添加到 gpio 組
sudo usermod -a -G gpio $USER

# 使用 sudo 運行（臨時）
sudo python main.py
```

#### API 無法訪問

```bash
# 檢查端口
netstat -tulpn | grep 8080

# 測試本地連接
curl http://localhost:8080/api/health

# 檢查防火牆
sudo ufw status
```

## Python API 使用

### 基本示例

```python
from scripts.api_example import SmartDormClient

# 創建客戶端
client = SmartDormClient("http://localhost:8080")

# 獲取狀態
status = client.get_status()
print(f"Person present: {status['data']['person_present']}")

# 控制燈光
client.set_light_state(True)  # 開燈
client.set_light_state(False)  # 關燈

# 觸發 WOL
client.trigger_wol()

# 獲取統計
stats = client.get_statistics()
print(stats['data']['detection'])
```

### 持續監控

```python
import time

client = SmartDormClient()

while True:
    status = client.get_status()['data']
    print(f"Person: {status['person_present']}, Light: {status['light_state']}")
    time.sleep(1)
```

## 性能優化

### 調整配置

```yaml
# 降低分辨率提高速度
camera:
  width: 320
  height: 240

# 降低檢測信心度（更靈敏）
pose_detection:
  min_detection_confidence: 0.5

# 增大緩衝區（更平滑）
presence:
  buffer_size: 10
```

### 監控性能

```bash
# 查看 FPS 報告
grep "Performance:" LOG/visiondorm_*.log | tail -20

# 實時監控
tail -f LOG/visiondorm_*.log | grep -E "FPS|Performance"
```

## 備份和恢復

### 備份配置

```bash
# 備份配置
cp visiondetect/configs/default.yaml ~/smartdorm_config_backup.yaml

# 備份日誌
tar -czf ~/smartdorm_logs_$(date +%Y%m%d).tar.gz LOG/
```

### 恢復配置

```bash
# 恢復配置
cp ~/smartdorm_config_backup.yaml visiondetect/configs/default.yaml

# 重啟服務
sudo systemctl restart visiondorm.service
```

## 更新

### 更新到新版本

```bash
# 1. 備份配置
cp visiondetect/configs/default.yaml ~/config_backup.yaml

# 2. 拉取更新
git pull origin main

# 3. 更新依賴
pip install -r requirements.txt

# 4. 恢復配置
cp ~/config_backup.yaml visiondetect/configs/default.yaml

# 5. 重啟服務
sudo systemctl restart visiondorm.service
```

## 開發

### 添加自定義檢測器

```python
from visiondetect.core.interfaces import Detector

class MyDetector(Detector):
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
        return {'detected': True}
```

### 運行測試

```bash
# 未來版本將提供
python -m pytest tests/
```

## 資源

### 文檔
- [README.md](README.md) - 主要文檔
- [ARCHITECTURE.md](ARCHITECTURE.md) - 架構文檔
- [CHANGELOG.md](CHANGELOG.md) - 變更日誌

### 工具
- `main.py` - 主程序
- `scripts/health_check.py` - 健康檢查
- `scripts/api_example.py` - API 示例
- `deploy_v2.sh` - 部署腳本

### 配置
- `visiondetect/configs/default.yaml` - 默認配置
- `requirements.txt` - Python 依賴

## 支持

### 問題報告
- GitHub Issues: https://github.com/dong881/VisionDetect_SmartDorm/issues

### 日誌提交
報告問題時，請提供：
1. 系統信息 (`uname -a`)
2. Python 版本 (`python --version`)
3. 健康檢查輸出
4. 相關日誌片段

```bash
# 收集信息
echo "=== System Info ===" > debug_info.txt
uname -a >> debug_info.txt
python --version >> debug_info.txt
echo "=== Health Check ===" >> debug_info.txt
python scripts/health_check.py >> debug_info.txt 2>&1
echo "=== Recent Logs ===" >> debug_info.txt
tail -100 LOG/visiondorm_*.log >> debug_info.txt
```

---

**提示**: 使用 `Ctrl+F` 或瀏覽器搜索功能快速查找所需命令。
