# DQA Environmental Standard Checker - 內部網路部署需求

## 📋 應用程式概述

| 項目 | 說明 |
|-----|------|
| **名稱** | DQA Environmental Standard Checker (法規標準檢查系統) |
| **用途** | 追蹤與驗證國際環境法規標準的版本與價格 |
| **使用者** | DQA 團隊成員 |
| **存取方式** | 網頁瀏覽器 (Chrome/Edge) |

---

## 🖥️ 伺服器需求

### 選項 A：Windows 伺服器（推薦）

| 需求 | 規格 |
|-----|------|
| 作業系統 | Windows Server 2016+ / Windows 10+ |
| Python | 3.10 或以上 |
| 記憶體 | 最少 2GB RAM |
| 硬碟 | 1GB 可用空間 |
| 網路 | 需能存取外部網站 (標準來源網站) |
| Port | 8001 (或其他可用 Port) |
| Chrome | 需安裝 Google Chrome (爬蟲功能使用) |

### 選項 B：Linux 伺服器

| 需求 | 規格 |
|-----|------|
| 作業系統 | Ubuntu 20.04+ / CentOS 7+ |
| Python | 3.10 或以上 |
| 記憶體 | 最少 2GB RAM |
| 硬碟 | 1GB 可用空間 |
| 網路 | 需能存取外部網站 |
| Port | 8001 (或其他可用 Port) |
| Chrome/Chromium | 需安裝 (爬蟲功能使用) |

### 選項 C：Docker 容器

如有 Docker 環境，可提供 Docker image 部署。

---

## 🔒 安全性考量

| 項目 | 說明 |
|-----|------|
| 對外連線 | 應用程式需連線至外部法規標準網站進行資料更新 |
| 防火牆規則 | 需允許 outbound HTTPS (443) 連線 |
| 內部存取 | 建議限制在公司內網存取 |

---

## 📡 Confluence 整合

部署完成後，可透過以下方式整合至 Confluence：

```html
<!-- 在 Confluence 頁面中使用 HTML 宏嵌入 -->
<iframe src="http://[伺服器IP]:8001" 
        width="100%" 
        height="800px" 
        frameborder="0">
</iframe>
```

---

## ❓ 請 IT 部門確認

1. □ 是否有可用的 Windows/Linux 伺服器？
2. □ 伺服器是否可安裝 Python 3.10+？
3. □ 是否可開放一個內部使用的 Port（如 8001）？
4. □ 伺服器是否可存取外部網站？
5. □ 是否支援 Docker 部署？
6. □ Confluence 是否允許 iframe 嵌入？

---

## 📞 聯絡資訊

如有技術問題，請聯繫應用程式負責人。
