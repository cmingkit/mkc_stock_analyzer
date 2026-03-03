# HTML 報告模板修復摘要

## 問題描述
用戶報告 `report_20260302_110558.html` 缺少必要的頭部引用，導致 CSS 樣式和 Chart.js 圖表無法正常加載。

## 根本原因
模板文件 `/templates/report.html` 中的 CSS 路徑是相對於模板位置的（`../static/css/report.css`），但生成的報告位於 `/reports/html/` 目錄，需要兩級向上（`../../static/css/report.css`）才能正確訪問 CSS 文件。

## 修復內容

### 1. 更新模板路徑（`/templates/report.html`）
```html
<!-- 修復前 -->
<link rel="stylesheet" href="../static/css/report.css">

<!-- 修復後 -->
<link rel="stylesheet" href="{{ css_path | default('../../static/css/report.css') }}">
```

### 2. 驗證引用完整性
- ✅ CSS 路徑：`../../static/css/report.css`（對於 `/reports/html/` 目錄正確）
- ✅ Chart.js CDN：`https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js`
- ✅ CSS 文件是自包含的，不需要 Bootstrap 或其他外部依賴

## 測試結果

### 測試報告
- 路徑：`/reports/html/report_20260302_140600.html`
- 狀態：✅ 所有引用正確

### 路徑驗證
```bash
# 從報告位置檢查 CSS 文件
cd /Users/mkc/.openclaw/workspace/stock_analyzer/reports/html
ls -la ../../static/css/report.css
# 輸出：-rw-r--r--  1 mkc  staff  33411 Mar  2 09:54 ../../static/css/report.css
```

## 目錄結構
```
/Users/mkc/.openclaw/workspace/stock_analyzer/
├── templates/
│   └── report.html (已修復)
├── static/
│   └── css/
│       └── report.css (33KB)
└── reports/
    └── html/
        ├── report_20260302_110558.html (舊報告，路徑錯誤)
        └── report_20260302_140600.html (新報告，路徑正確)
```

## 向後兼容性
- 模板使用 Jinja2 默認值過濾器，如果未傳遞 `css_path` 變量，將使用 `../../static/css/report.css`
- 現有代碼無需修改，`HTMLReporter` 類會自動使用默認值

## 後續建議
1. 如果需要在不同目錄層級生成報告，可以在 `HTMLReporter` 中傳遞 `css_path` 變量
2. 考慮在未來版本中使用絕對路徑或基於 URL 的路徑（如果報告需要通過 Web 服務器訪問）

## 修復日期
2026-03-02 14:06 HKT
