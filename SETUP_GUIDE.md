# Stock Analyzer - GitHub Pages 設置指南

## 快速開始

### 1. 創建 GitHub Repository

```bash
# 在 GitHub 上創建新 repository
# 名稱：stock_analyzer
# 設為 Public（GitHub Pages 需要）

# 推送到 GitHub
cd ~/claw-code/stock_analyzer
git remote add origin https://github.com/YOUR_USERNAME/stock_analyzer.git
git push -u origin main
```

### 2. 設置 GitHub Secrets

前往 **Settings → Secrets and variables → Actions → New repository secret**

#### 必需 Secrets（如果要使用 Telegram 推送）

| Name | Value |
|------|-------|
| `TELEGRAM_BOT_TOKEN` | 你的 Telegram Bot Token |
| `TELEGRAM_CHAT_ID` | 你的 Telegram Chat ID |

#### 可選 Secrets（如果要使用 Reddit 數據）

| Name | Value |
|------|-------|
| `REDDIT_CLIENT_ID` | Reddit App Client ID |
| `REDDIT_CLIENT_SECRET` | Reddit App Secret |
| `REDDIT_USER_AGENT` | 例如：StockAnalyzer/1.0 by yourname |

### 3. 啟用 GitHub Pages

1. 前往 **Settings → Pages**
2. **Source**: Deploy from a branch
3. **Branch**: main
4. **Folder**: /docs
5. 點擊 **Save**

### 4. 觸發首次運行

前往 **Actions → Daily Stock Analysis → Run workflow → Run workflow**

### 5. 訪問報告

```
https://YOUR_USERNAME.github.io/stock_analyzer/
```

## 本地測試

```bash
# 1. 安裝依賴
cd ~/claw-code/stock_analyzer
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. 配置 secrets
cp config/secrets.yaml.example config/secrets.yaml
# 編輯 config/secrets.yaml

# 3. 運行分析
PYTHONPATH=. python src/main.py --mode daily --output-dir docs/reports --no-telegram

# 4. 生成索引
python scripts/generate_index.py

# 5. 本地預覽
cd docs
python -m http.server 8080
# 訪問 http://localhost:8080
```

## 驗證清單

- [ ] Git repo 已初始化
- [ ] GitHub Actions workflow 已創建
- [ ] GitHub Secrets 已設置
- [ ] GitHub Pages 已啟用（/docs 目錄）
- [ ] 首次 workflow 運行成功
- [ ] 報告頁面可訪問

## 常見問題

### Q: GitHub Actions 失敗怎麼辦？

A: 
1. 檢查 Actions 頁面的錯誤日誌
2. 確認 requirements.txt 可正常安裝
3. 確認所有必要的 Secrets 已設置

### Q: 報告頁面 404？

A:
1. 確認 GitHub Pages 已啟用
2. 確認選擇的是 /docs 目錄
3. 等待 5-10 分鐘讓部署完成

### Q: 如何修改定時執行時間？

A: 編輯 `.github/workflows/daily-analysis.yml`：

```yaml
on:
  schedule:
    - cron: '0 23 * * *'  # UTC 23:00 = HKT 07:00
```

Cron 時間對照：
- HKT 07:00 = UTC 23:00 = `0 23 * * *`
- HKT 12:00 = UTC 04:00 = `0 4 * * *`
- HKT 18:00 = UTC 10:00 = `0 10 * * *`

### Q: 如何添加更多股票？

A: 編輯 `config/stocks.yaml`：

```yaml
tech:
  - AAPL
  - GOOGL
  - MSFT

custom:
  - YOUR_STOCK
```

## 支持

如有問題，請在 GitHub 上提交 Issue。
