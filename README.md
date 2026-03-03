# Stock Analyzer - GitHub Pages 版本

[![Daily Analysis](https://github.com/YOUR_USERNAME/stock_analyzer/actions/workflows/daily-analysis.yml/badge.svg)](https://github.com/YOUR_USERNAME/stock_analyzer/actions/workflows/daily-analysis.yml)

自動化的股票分析系統，每日生成報告並發布到 GitHub Pages。

## 功能

- 📊 每日自動分析熱門股票
- 📈 技術面 + 基本面分析
- 🤖 Reddit 情緒分析
- 📱 Telegram 推送（可選）
- 🌐 GitHub Pages 公開報告

## 設置步驟

### 1. Fork 或 Clone 本倉庫

```bash
git clone https://github.com/YOUR_USERNAME/stock_analyzer.git
cd stock_analyzer
```

### 2. 設置 GitHub Secrets

前往 **Settings → Secrets and variables → Actions**，添加以下 secrets：

| Secret Name | 說明 | 必填 |
|------------|------|------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | 否（如需推送） |
| `TELEGRAM_CHAT_ID` | Telegram Chat ID | 否（如需推送） |
| `REDDIT_CLIENT_ID` | Reddit App Client ID | 否（如需 Reddit 數據） |
| `REDDIT_CLIENT_SECRET` | Reddit App Secret | 否（如需 Reddit 數據） |
| `REDDIT_USER_AGENT` | Reddit User Agent | 否（如需 Reddit 數據） |

#### 如何獲取 Telegram Bot Token

1. 在 Telegram 中找到 [@BotFather](https://t.me/botfather)
2. 發送 `/newbot` 創建新機器人
3. 按提示設置名稱，獲取 Token

#### 如何獲取 Telegram Chat ID

1. 在 Telegram 中找到 [@userinfobot](https://t.me/userinfobot)
2. 發送任意消息，獲取你的 Chat ID

### 3. 啟用 GitHub Pages

前往 **Settings → Pages**：

- **Source**: Deploy from a branch
- **Branch**: main
- **Folder**: /docs

點擊 **Save**，等待幾分鐘後即可訪問。

### 4. 手動觸發或等待自動執行

- **手動觸發**：前往 **Actions → Daily Stock Analysis → Run workflow**
- **自動執行**：每天 HKT 07:00（UTC 23:00）自動運行

## 訪問報告

設置完成後，訪問：

```
https://YOUR_USERNAME.github.io/stock_analyzer/
```

## 本地開發

### 安裝依賴

```bash
# 創建虛擬環境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安裝依賴
pip install -r requirements.txt
```

### 配置

```bash
# 複製配置範例
cp config/secrets.yaml.example config/secrets.yaml

# 編輯配置文件
nano config/secrets.yaml
```

### 運行分析

```bash
# 運行每日分析（輸出到 docs/reports）
PYTHONPATH=. python src/main.py --mode daily --output-dir docs/reports --no-telegram

# 生成本地預覽
python scripts/generate_index.py

# 本地預覽（需要 Python HTTP server）
cd docs
python -m http.server 8080
# 訪問 http://localhost:8080
```

## 項目結構

```
stock_analyzer/
├── .github/
│   └── workflows/
│       └── daily-analysis.yml    # GitHub Actions workflow
├── docs/                          # GitHub Pages 根目錄
│   ├── index.html                # 報告列表首頁
│   ├── reports/                  # HTML 報告存放
│   ├── static/                   # CSS/JS 文件
│   └── .nojekyll                 # 禁用 Jekyll
├── src/                          # 源代碼
│   ├── main.py                   # 主程序
│   ├── collectors/               # 數據收集
│   ├── analyzers/                # 分析模組
│   └── reporters/                # 報告生成
├── config/
│   ├── stocks.yaml               # 股票列表
│   └── secrets.yaml.example      # 配置範例
├── scripts/
│   └── generate_index.py         # 生成報告索引
├── requirements.txt
├── .gitignore
└── README.md
```

## 自定義分析

### 添加股票

編輯 `config/stocks.yaml`：

```yaml
tech:
  - AAPL
  - GOOGL
  - MSFT

financial:
  - JPM
  - BAC
  - WFC

# 添加更多類別...
```

### 修改分析參數

編輯 `src/main.py` 中的參數：

- `--mode`: 分析模式（daily/alerts/weekly）
- `--stocks`: 指定股票（可選）
- `--format`: 報告格式（html/pdf/json）

## 故障排除

### GitHub Actions 失敗

1. 檢查 **Actions** 頁面的錯誤日誌
2. 確認所有必要的 Secrets 已設置
3. 確認 `requirements.txt` 中的依賴可安裝

### GitHub Pages 404

1. 確認 **Settings → Pages** 已啟用
2. 確認 `docs/` 目錄存在
3. 等待幾分鐘讓部署完成

### 報告無法生成

1. 檢查 `config/secrets.yaml` 是否正確
2. 檢查 API 限額（Reddit/Alpha Vantage）
3. 查看本地日誌：`logs/app.log`

## 授權

MIT License

## 貢獻

歡迎提交 Issue 和 Pull Request！

---

**⚠️ 免責聲明**：本工具僅供學習和研究用途，不構成投資建議。投資有風險，請謹慎決策。
