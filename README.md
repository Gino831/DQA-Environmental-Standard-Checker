# 🌿 DQA Environmental Standard Checker

法規標準檢查系統 - 環境法規管理與追蹤工具

## 🚀 一鍵啟動

**Windows 使用者：**

雙擊執行 `一鍵安裝與啟動.bat` 即可自動完成以下步驟：
1. 檢查 Python 環境
2. 安裝相依套件
3. 啟動伺服器並開啟瀏覽器

---

## 📋 系統需求

- **Python 3.8+** - [下載連結](https://www.python.org/downloads/)
- 安裝時請勾選 **"Add Python to PATH"**

---

## ✨ 功能特色

### 📊 儀表板
| 功能 | 說明 |
|------|------|
| Expiring This Year | 顯示今年即將到期的法規數量 |
| Est. Upgrade Cost | 預估升級費用（支援 TWD 匯率轉換）|
| 一鍵更新 | 從官方網站自動抓取最新資訊 |

### 📋 法規管理
- ✅ **新增法規** - 支援多種分類（MOXA、Marine、Railway、Power Station）
- ✅ **檢視詳情** - 查看法規完整資訊
- ✅ **編輯法規** - 修改現有法規資料
- ✅ **刪除法規** - 移除不需要的法規
- ✅ **搜尋過濾** - 即時搜尋法規名稱/描述

### 🌐 網路爬蟲
支援以下標準組織網站的自動資料抓取：
- IEC (國際電工委員會)
- BSI (英國標準協會)
- DNV (挪威船級社)
- NEMA (美國電氣製造商協會)

---

## 📁 專案結構

```
DQA Environmental Standard Checker/
├── 一鍵安裝與啟動.bat   # 🚀 一鍵啟動腳本
├── index.html            # 前端頁面
├── app.js                # 前端邏輯
├── style.css             # 樣式表
├── data.js               # 法規資料
├── server.py             # Python HTTP 伺服器
├── verify_standards.py   # 網路爬蟲腳本
└── requirements.txt      # Python 相依套件
```

---

## 🛠️ 手動安裝

若自動安裝失敗，請依以下步驟手動安裝：

```bash
# 1. 安裝相依套件
pip install -r requirements.txt

# 2. 啟動伺服器
python server.py

# 3. 開啟瀏覽器訪問
# http://127.0.0.1:8000
```

---

## 📞 支援

如有問題，請聯繫 DQA 團隊。

---

**版本**: 1.0.0  
**最後更新**: 2026-01-15
