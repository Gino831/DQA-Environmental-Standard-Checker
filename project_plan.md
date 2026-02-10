# DQA 環境法規標準檢查工具 - 系統建置與驗證計畫書

## 1. 專案概述 (Project Overview)
本計畫旨在建立一套高效、準確的「DQA 環境法規標準檢查工具」，協助團隊管理 IEC、ISO、EN 等國際法規標準。本系統解決了人工追蹤法規版本耗時、易出錯且難以即時掌握改版資訊的痛點，確保產品測試始終依據最新的國際標準進行。

## 2. 專案目標 (Objectives)
1.  **資料正確性 (Accuracy)**：確保所有法規的版本、發行日期、穩定性日期 (Stability Date) 及購買成本與官方來源 (IEC Webstore) 100% 一致。
2.  **即時性 (Timeliness)**：提供自動化檢查機制，快速識別過期或即將改版的法規。
3.  **可視化 (Visibility)**：透過儀表板 (Dashboard) 即時呈現法規狀態與預估維護成本。
4.  **可驗證性 (Verifiability)**：建立標準作業程序 (SOP) 與系統輔助功能，讓使用者能隨時「一鍵查證」資料來源。

## 3. 技術架構 (Technical Architecture)

### 3.1 前端 (Frontend)
*   **技術棧**：HTML5, CSS3 (Vanilla CSS), JavaScript (ES6+)。
*   **設計風格**：採用 Glassmorphism (毛玻璃) 設計語彙，提供現代化、直觀的使用者介面。
*   **圖示庫**：Lucide Icons。
*   **特點**：
    *   **無框架依賴**：不使用 React/Vue 等重型框架，確保輕量化與易維護性。
    *   **響應式設計**：支援桌面與平板瀏覽。
    *   **動態渲染**：透過 JS 動態生成表格與模態視窗 (Modal)。

### 3.2 後端 (Backend)
*   **技術棧**：Python 3.x。
*   **核心組件**：
    *   **`verify_standards.py`**：自動化爬蟲腳本。使用 `requests` 與 `BeautifulSoup` 抓取 IEC 官方網站數據。
    *   **`server.py`**：輕量級 HTTP 伺服器 (基於 `http.server`)。負責託管前端頁面並提供 API 接口 (`/api/run-verify`) 以觸發 Python 腳本。
*   **功能**：
    *   執行即時網頁爬取。
    *   比對本地資料與線上最新版本。
    *   生成驗證報告 (`verification_report.md`) 與 JSON 結果 (`verification_results.json`)。

### 3.3 資料庫 (Database)
由於本系統定位為輕量級工具，不使用傳統關聯式資料庫 (SQL)，採用以下混合儲存策略：
*   **初始資料 (`data.js`)**：定義系統預設的標準法規清單，作為 "Source of Truth" 的備份。
*   **瀏覽器儲存 (`localStorage`)**：用於持久化使用者的操作（如新增、修改、刪除的法規），確保關閉瀏覽器後資料不丟失。
*   **交換格式 (`JSON`)**：後端爬蟲生成的結果以 JSON 格式傳遞給前端進行渲染。

## 4. 實現流程 (Implementation Steps)

1.  **資料結構設計**：定義法規物件的核心欄位 (ID, Name, Version, Effective Date, Expiry Date, Cost, Source URL)。
2.  **前端開發**：
    *   建置 `index.html` 骨架與 `style.css` 樣式。
    *   實作 `app.js` 處理資料載入、表格渲染、搜尋過濾與 CRUD (新增/修改/刪除) 邏輯。
3.  **後端自動化開發**：
    *   撰寫 `verify_standards.py`，實作針對 IEC 網站的爬蟲邏輯。
    *   設計版本比對演算法，識別 Version, Date, Cost 的變更。
4.  **系統整合**：
    *   開發 `server.py` 串接前後端。
    *   前端實作 "Verify & Load Report" 按鈕，呼叫後端 API 並解析回傳的 JSON 報告。
5.  **一鍵部署**：製作 `start_app.bat` 批次檔，整合啟動流程。

## 5. 核心功能 (Core Features)
*   **儀表板 (Dashboard)**：即時顯示過期法規數量與預估升級成本。
*   **法規管理**：支援分類檢視、搜尋、新增、編輯、刪除。
*   **智能驗證**：一鍵聯網檢查最新版本，自動標示差異 (Mismatch)。
*   **官方查證**：提供直連官方網站的連結，方便人工複核。

## 6. 系統演示 (Demo)

本系統已封裝為一鍵執行版本，操作步驟如下：

1.  **啟動系統**：
    *   在專案資料夾中找到 **`start_app.bat`** 檔案。
    *   **雙擊執行**。
    *   系統將自動啟動 Python 伺服器，並開啟預設瀏覽器進入儀表板。

2.  **執行驗證 (Verify)**：
    *   在儀表板上方點擊 **"Verify & Load Report"** 按鈕。
    *   系統將在背景執行爬蟲 (約需數秒至數分鐘)。
    *   完成後，畫面將彈出「差異報告」，列出所有需要更新的法規。

3.  **更新資料**：
    *   在差異報告中確認變更項目。
    *   點擊 **"Update All"**，系統將自動將最新資訊寫入本地資料庫。

## 7. 結論 (Conclusion)
本系統透過「前端輕量化、後端自動化」的架構，成功實現了環境法規的智慧管理。透過 `start_app.bat` 的一鍵整合，大幅降低了使用門檻，讓 DQA 團隊能隨時掌握最新的國際標準動態。
