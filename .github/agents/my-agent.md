---
name: SmartDorm Guardian Agent
description: 一個可模組化、可擴充、具自動測試與CI/CD的宿舍願景偵測管家型Agent，確保功能迭代時維持向後相容，並能自動部署與回報問題後持續修復。
---

# SmartDorm Guardian Agent Blueprint

本設計藍圖以 VisionDetect_SmartDorm 專案為基礎，提供可擴充、具備自動化測試與CI/CD能力的 Agent 架構，目標是在新增/修改功能時不影響既有功能，並透過自動化流程持續迭代直到問題修復與功能穩定。

## 1. 簡介
- 目標：
  - 以模組化架構管理偵測流程（資料擷取、前處理、模型推論、規則判定、告警/回報、日誌與監控）。
  - 每次功能變更皆以單元測試與整合測試驗證回歸不出現。
  - 以 GitHub Actions 建立 CI（測試/分析/建置）與 CD（封裝/部署）管線，自動回報錯誤並驅動修復迭代。
  - 支援 Feature Flags 與版本化策略，保障舊功能穩定。

## 2. 主要架構（模組化與可擴充）
建議以資料夾/套件劃分關注點，彼此以清晰介面溝通：

```
visiondetect_smartdorm/
├─ agents/
│  ├─ core/                  # Agent 核心協調器 (任務管理、事件匯流排)
│  │  ├─ orchestrator.py
│  │  ├─ router.py            # 按規則/特徵路由到不同能力模組
│  │  └─ interfaces.py        # 能力模組標準介面定義
│  ├─ capabilities/           # 能力模組（可外掛/可替換）
│  │  ├─ ingestion.py         # 視訊/影像/感測資料擷取
│  │  ├─ preprocessing.py     # 影像前處理(去噪、校正、ROI)
│  │  ├─ detection.py         # 物件/姿態/異常偵測（模型抽象層）
│  │  ├─ postprocess.py       # 規則引擎、閾值、追蹤
│  │  ├─ notifier.py          # 告警通報(Email/Slack/Webhook)
│  │  ├─ storage.py           # 結果與日誌存取
│  │  └─ monitoring.py        # 健康檢查與指標暴露
│  └─ plugins/                # 新功能以外掛形式新增 (約定介面)
├─ configs/
│  ├─ default.yaml            # 預設設定(可用環境變數覆寫)
│  ├─ feature_flags.yaml      # 功能旗標 (開啟/灰度/回滾)
│  └─ models.yaml             # 模型版本/權重位置/閾值
├─ tests/
│  ├─ unit/                   # 單元測試
│  ├─ integration/            # 整合與端對端測試(E2E)
│  └─ data/                   # 測試樣本(小型、匿名化)
├─ scripts/
│  ├─ run_agent.py            # 啟動入口（讀 config + 建構能力模組）
│  ├─ check_health.py
│  └─ migrate_assets.py
├─ ci/
│  ├─ github-actions/         # CI/CD YAML 範本
│  └─ quality/                # 規範(ruff/flake8/black/mypy)
├─ Dockerfile
├─ pyproject.toml / requirements.txt
└─ README.md
```

設計重點：
- 以 interfaces.py 定義抽象基底類（Capability、Detector、Notifier等），讓新功能只需實作介面即可插入。
- router.py 根據 feature_flags.yaml、場景規則與輸入中繼資料動態選擇模組，減少硬耦合。
- capabilities/detection.py 僅暴露「推論介面」，實際模型以策略模式註冊（例：YOLO、OpenVINO、ONNXRuntime、TensorRT）。
- 以 Semantic Versioning（主.次.修）管理功能版本，並在 configs/models.yaml 中標注模型版本與回滾策略。

## 3. 測試策略（避免回歸）
- 單元測試（pytest）：
  - 對每個能力模組建立最小可重現測試，替代外部資源以 mock/fake。
  - 驗證介面契約不變（輸入/輸出型別與欄位）。
- 合約測試（Contract Test）：
  - 測試 capabilities 對 orchestrator 的介面，確保升級不破壞呼叫方。
- 整合測試（Integration/E2E）：
  - 使用小型測試影像/影片樣本，驗證從 ingestion → detection → postprocess → notifier 的完整流程。
  - 對常見場景（有人/無人、夜間/光害、遮擋）提供固定基準輸出（golden files）。
- 效能與穩定性：
  - 在 CI 中記錄推論時間與記憶體趨勢，設定警戒門檻（例如P95延遲）。
- 回歸門檻：
  - 若既有測試失敗或效能退化超過門檻，禁止合併（required checks）。

範例測試（pytest）：
```python
# tests/unit/test_detection_contract.py
from agents.core.interfaces import Detector
from agents.capabilities.detection import get_detector

def test_detector_interface_contract():
    det = get_detector(model_name="yolo-lite", version="1.2.0")
    assert isinstance(det, Detector)
    out = det.infer(image=b"fake-bytes")
    assert "boxes" in out and "scores" in out
    assert isinstance(out["boxes"], list)
```

## 4. CI/CD 流程（GitHub Actions 範例）
以下提供最小可行 YAML，請放置於 .github/workflows/ci.yml：

```yaml
name: CI
on:
  pull_request:
    branches: [ master, main ]
  push:
    branches: [ master ]
jobs:
  test-and-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - name: Install deps
        run: |
          pip install -U pip
          pip install -r requirements.txt
          pip install pytest pytest-cov ruff mypy
      - name: Lint & Type Check
        run: |
          ruff check .
          mypy visiondetect_smartdorm || true  # 可先容忍型別警告，逐步收斂
      - name: Run tests
        run: |
          pytest -q --maxfail=1 --disable-warnings --cov=visiondetect_smartdorm
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        if: success()
        with:
          fail_ci_if_error: true

  build-and-package:
    needs: test-and-quality
    if: github.ref == 'refs/heads/master'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker image
        run: |
          docker build -t ghcr.io/${{ github.repository }}:${{ github.sha }} .
      - name: Login GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - name: Push Image
        run: |
          docker push ghcr.io/${{ github.repository }}:${{ github.sha }}
```

若需要自動部署（CD），可新增 .github/workflows/deploy.yml：

```yaml
name: Deploy
on:
  workflow_run:
    workflows: ["CI"]
    types: ["completed"]
    branches: [ master ]
jobs:
  deploy:
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    runs-on: ubuntu-latest
    steps:
      - name: Deploy via SSH/ArgoCD/K8s
        run: |
          echo "Replace with real deploy steps (kubectl/helm/argo rollout)"
```

## 5. 自動回報與修復迭代
- 失敗自動回報：
  - 使用 GitHub Actions 的 annotations 與 status check；
  - 透過 Issue/PR 自動留言機器人（例如 actions/github-script）回報失敗模組、日誌與建議修復步驟；
  - 可整合 Slack/Webhook 通知（notifier 模組重用）。
- 自動建立追蹤議題：
```yaml
- name: Open issue on failure
  if: failure()
  uses: actions/github-script@v7
  with:
    script: |
      const title = `CI 失敗於 ${process.env.GITHUB_SHA.substring(0,7)}`;
      const body = `請檢查工作流程日誌，優先模組：detection/preprocess/notifier。`;
      await github.rest.issues.create({
        owner: context.repo.owner,
        repo: context.repo.repo,
        title,
        body,
        labels: ['ci-failure','bug']
      });
```
- 修復迭代：
  - PR 需新增/更新測試，覆蓋修復與新案例；
  - 啟用 Feature Flag 做灰度釋出，觀察監控指標（monitoring 模組）；
  - 若指標退化，自動回滾到前一版容器映像與模型設定。

## 6. 新功能的安全增量策略
- Feature Flags：新功能預設 off，僅 E2E 通過且穩定後逐步放量。
- 版本化與變更日誌：維持 CHANGELOG 與模型版本對照，先行支援雙路徑（舊/新）並行一段時間。
- 合約守護：任何破壞性變更需標註 deprecation 週期，提供適配層。

## 7. 持續優化與自動化流程建議
- 靜態分析：ruff + mypy + bandit（安全檢查）。
- 模型治理：
  - 在 models.yaml 管理多模型版本與閾值，提供 A/B 測試能力。
  - 以資料漂移檢測（如 KL divergence/PSI）觸發重新校準或重新訓練工作流。
- 效能監控：
  - 暴露 Prometheus 指標（FPS、延遲、偵測數量、錯誤率），以 Grafana 觀察。
- 資產管理：
  - 以 DVC/MLflow 追蹤資料與模型；PR 需對應模型變更紀錄。
- 發布策略：
  - 使用 semantic-release 或手動標註 tag，CI 自動產生發行說明與對應容器標籤。

## 8. 快速開始
- 安裝：`pip install -r requirements.txt`
- 執行：`python scripts/run_agent.py --config configs/default.yaml`
- 測試：`pytest -q`
- 本地 Docker：`docker build -t smartdorm-agent:dev . && docker run --rm smartdorm-agent:dev`

---
此藍圖可作為後續擴充的基礎，確保每次修改都有測試保護與自動化部屬回饋，最終達到穩定迭代與正確新增功能。
