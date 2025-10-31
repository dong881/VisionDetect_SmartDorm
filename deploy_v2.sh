#!/bin/bash

set -e

echo "=========================================="
echo "VisionDetect SmartDorm 自動部署腳本 v2.0"
echo "=========================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONDA_ENV="mediapipe-env"
echo "專案目錄: $SCRIPT_DIR"
echo "Conda 環境名稱: $CONDA_ENV"
echo ""

# 1. 檢查並安裝 Miniconda
echo "[步驟 1/7] 檢查 Miniconda..."
if command -v conda &>/dev/null; then
    echo "✓ Miniconda 已安裝"
else
    echo "下載並安裝 Miniconda..."
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh
    chmod +x Miniconda3-latest-Linux-aarch64.sh
    ./Miniconda3-latest-Linux-aarch64.sh -b -p $HOME/miniconda3
    rm Miniconda3-latest-Linux-aarch64.sh
    export PATH="$HOME/miniconda3/bin:$PATH"
    echo "✓ Miniconda 安裝完成"
fi
export PATH="$HOME/miniconda3/bin:$PATH"
echo ""

# 2. 檢查並建立 conda 環境
echo "[步驟 2/7] 檢查 conda 環境..."
if conda env list | grep -q "$CONDA_ENV"; then
    echo "✓ Conda 環境已存在: $CONDA_ENV"
else
    echo "建立 conda 環境: $CONDA_ENV 與 Python 3.12"
    conda create -n "$CONDA_ENV" python=3.12 -y
    echo "✓ Conda 環境建立完成"
fi
echo ""

# 3. 安裝必要套件
echo "[步驟 3/7] 安裝必要套件..."
eval "$(conda shell.bash hook)"
conda activate "$CONDA_ENV"
export TMPDIR=/home/$(whoami)
pip install --upgrade pip

# Install from requirements.txt
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    echo "從 requirements.txt 安裝套件..."
    pip install -r "$SCRIPT_DIR/requirements.txt"
fi

# Install additional packages
pip install RPi.GPIO

echo "✓ 所有套件安裝完成"
echo ""

# 4. 建立 LOG 目錄
echo "[步驟 4/7] 建立 LOG 目錄..."
mkdir -p "$SCRIPT_DIR/LOG"
echo "✓ LOG 目錄建立完成: $SCRIPT_DIR/LOG"
echo ""

# 5. 運行健康檢查
echo "[步驟 5/7] 執行系統健康檢查..."
if [ -f "$SCRIPT_DIR/scripts/health_check.py" ]; then
    python "$SCRIPT_DIR/scripts/health_check.py" || echo "⚠ 健康檢查發現一些問題，但將繼續安裝"
else
    echo "⚠ 健康檢查腳本未找到，跳過檢查"
fi
echo ""

# 6. 生成啟動 wrapper script
echo "[步驟 6/7] 建立啟動腳本..."
WRAPPER="$SCRIPT_DIR/run_visiondorm.sh"
cat > "$WRAPPER" <<EOF
#!/bin/bash
SCRIPT_DIR="$SCRIPT_DIR"
source \$HOME/miniconda3/etc/profile.d/conda.sh
conda activate $CONDA_ENV

# Use new main.py if available, fallback to old main-mediapipe.py
if [ -f "\$SCRIPT_DIR/main.py" ]; then
    exec python "\$SCRIPT_DIR/main.py"
else
    exec python "\$SCRIPT_DIR/main-mediapipe.py"
fi
EOF
chmod +x "$WRAPPER"
echo "✓ 啟動wrapper腳本建立完成: $WRAPPER"
echo ""

# 7. 建立 systemd 服務檔案
echo "[步驟 7/7] 建立 systemd 服務..."
SERVICE_FILE="/etc/systemd/system/visiondorm.service"
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=VisionDetect SmartDorm Service v2.0
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$SCRIPT_DIR
ExecStart=$WRAPPER
Restart=on-failure
RestartSec=5
StandardOutput=file:$SCRIPT_DIR/LOG/visiondorm.log
StandardError=file:$SCRIPT_DIR/LOG/visiondormError.log

[Install]
WantedBy=multi-user.target
EOF

echo "✓ 服務檔案建立完成: $SERVICE_FILE"
echo ""

# 啟用並啟動服務
echo "啟用並啟動服務..."
sudo systemctl daemon-reload
echo "✓ systemd 設定重新載入"
sudo systemctl enable visiondorm.service
echo "✓ 服務已設定為開機自動啟動"
sudo systemctl restart visiondorm.service
echo "✓ 服務已啟動"
echo ""

echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "服務狀態："
sudo systemctl status visiondorm.service --no-pager
echo ""
echo "實用指令："
echo "  檢查服務狀態: sudo systemctl status visiondorm.service"
echo "  停止服務:     sudo systemctl stop visiondorm.service"
echo "  重新啟動服務: sudo systemctl restart visiondorm.service"
echo "  查看日誌:     tail -f $SCRIPT_DIR/LOG/visiondorm.log"
echo "  查看錯誤日誌: tail -f $SCRIPT_DIR/LOG/visiondormError.log"
echo "  健康檢查:     python $SCRIPT_DIR/scripts/health_check.py"
echo ""
