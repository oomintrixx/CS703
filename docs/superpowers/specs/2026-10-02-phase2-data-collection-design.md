# Phase 2: Data Understanding — 設計文件

日期：2026-10-02
範圍：CRISP-DM Phase 2 的四個 task（2.1 Gathering Data、2.2 Describing Data、2.3 Exploring Data、2.4 Verifying Data Quality）與對應的四份 deliverable，合併成單一報告 `docs/phase2-data-understanding.md`。實際執行資料蒐集（非佔位資料），用真實數字撰寫報告。

## 範圍決定

- **時間範圍**：FY2026（2025-07-01 ~ 2026-06-30），NYC 最近一個已完整結束的會計年度。
- **地理範圍**：五區全部（不縮小到單一 borough）。
- **資料來源（5 個核心來源，其餘 5 個留待後續）**：
  1. Parking Violations Issued – Fiscal Year 2026（Socrata id `9mwx-gamw`，實測 15,691,604 筆）
  2. Parking Meters Locations and Status（Socrata id `693u-uax6`，實測 15,598 筆）
  3. NYPD Police Precincts 轄區邊界（Socrata id `y76i-bdw7`，78 筆，含 geometry）
  4. Open-Meteo 歷史逐小時天氣（archive-api.open-meteo.com，NYC 中央公園座標 40.7829, -73.9654，FY2026 整年）
  5. ~~ASP 停收日曆~~ — 確認無結構化 API（只有 PDF/網頁），本輪**不**蒐集，在 Data Quality Report 記錄為已知缺口。
- **Parking Violations 的抓法**：15.69M 筆全量下載到本地不划算（~60-90 分鐘、數 GB）。改用：
  - 伺服器端 SoQL `$group` 聚合（對全部 1569 萬筆做 count by borough / month / day-of-week / top violation codes）→ 準確、快、存成小檔案到 `data/processed/`。
  - 另外分頁抓 100 萬筆代表性樣本（`$limit`/`$offset`，約 20 次請求、~4 分鐘）存到 `data/raw/`，供 Phase 3 特徵工程與本地細部檢查使用。
  - `violation_time` 欄位是非標準文字格式（如 `"0225P"`），SoQL 無法直接轉換，小時分布統計改用本地樣本解析，報告中會註明這點（非全母體統計）。

## 程式碼結構

```
src/cs703/data/
├── socrata_client.py   # 共用：分頁抓取 + 重試/backoff，無 app token 也可運作
├── violations.py        # fetch_aggregates() 全母體聚合；fetch_sample(n) 分頁抽樣
├── meters.py             # fetch_meters() 全量下載
├── precincts.py          # fetch_precincts() 全量下載（GeoJSON）
└── weather.py            # fetch_weather(start, end) Open-Meteo 歷史天氣

scripts/
└── collect_data.py       # 主執行腳本：依序呼叫上述所有 fetcher，
                           # 寫入 data/raw/ 與 data/processed/，
                           # 並輸出 data/processed/collection_manifest.json
                           # （每個來源的筆數、檔案大小、抓取時間戳、來源 URL）
```

- `socrata_client.py` 提供 `fetch_all(resource_id, select=None, where=None, group=None, order=None, page_size=50_000, app_token=None)`，統一處理分頁與重試；`app_token` 從 `cs703.config.SOCRATA_APP_TOKEN` 讀取（可為 `None`，無 token 時速率較慢但仍可運作）。
- `collect_data.py` 是唯一的進入點，`uv run python scripts/collect_data.py` 即可重現整個蒐集流程；manifest 檔案是報告數字的唯一真實來源（報告裡的表格數字都從它或從下載後的檔案直接算出，不手動編造）。

## 報告結構（`docs/phase2-data-understanding.md`）

一份 Markdown 檔案，四個章節，只用文字與表格（不嵌圖）：

1. **Task 2.1 — Data Collection Report**：來源總表（資料集名稱/ID、存取方式、時間範圍、抓取筆數、檔案大小、抓取時間戳）、已知缺口（ASP 日曆）、重現步驟。
2. **Task 2.2 — Data Description Report**：每個資料集的欄位表（欄位名、型別、非空率）、列數、時間/地理涵蓋範圍、檔案格式與大小。
3. **Task 2.3 — Data Exploration Report**：表格呈現 — 違規數依 borough、依月份（季節性）、依星期幾、依小時（樣本）、前 15 大違規代碼；meters 依 borough 分布；天氣月平均溫度/降水。
4. **Task 2.4 — Data Quality Report**：缺值率、重複列檢查、異常值（如 `violation_precinct = "0"`、borough 代碼不一致、座標超出 NYC 範圍）、日期範圍完整性檢查、ASP 日曆缺口正式記錄、整體問題清單（issue log 表格）。

## 明確排除範圍

- 不蒐集本輪外的 5 個次要來源（Open Parking and Camera Violations、ParkNYC rates、LION street centerline、NYC Permitted Events、Ticketmaster）。
- 不處理 ASP 停收日曆（記錄為缺口，非本輪交付）。
- 不產生圖表/notebook，報告純文字 + 表格。
- 不下載 Parking Violations 全量 1569 萬筆到本地（只存聚合結果 + 100 萬筆樣本）。
