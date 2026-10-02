# CS703 專案骨架設計

日期：2026-10-02
範圍：為「Predicting Parking Pressure Across New York City」專案（CRISP-DM 方法論，單人研究者，Fall 2026）建立初始 repo 骨架。**不**包含任何 Phase 2 資料蒐集的實際程式碼。

## 背景

`cs703` repo 目前只有一個空的 README。專案的 Phase 1（Business Understanding）文件已經在 `/Users/alicec/Desktop/wei/monroeu/fall 2026/CS703/` 底下完成，分別是：

- `CS703_Phase1_Business_Understanding.docx` — 正式的 CRISP-DM Phase 1 文件（business objectives、stakeholders、data-mining goals、14 週專案計畫）
- `Data_Science_Project_Proposal_Parking_NYC.docx` — 搭配的專案提案（violation-density 作為 parking pressure 的代理指標）

另有一份 `Project_Proposal.docx` 是較早的舊構想（假設有 sensor/meter 即時佔用資料），方向與目前的 violation-density proxy 方法不一致，本次**不**收錄進 repo。

核心建模方向：用 NYC 公開的 parking violation 密度，結合 meter 資訊、街道地理、時間特徵、天氣、活動資料，預測一個區域在特定時間窗口的 parking pressure（High/Medium/Low），並需要把「執法強度」跟「真實需求」分開（enforcement normalization）。

## 目錄結構

```
cs703/
├── README.md
├── pyproject.toml
├── uv.lock
├── .python-version
├── .env.example
├── .gitignore
├── docs/
│   ├── superpowers/specs/              # 本設計文件所在位置
│   ├── phase1-business-understanding.md
│   └── project-proposal.md
├── data/
│   ├── raw/.gitkeep
│   ├── interim/.gitkeep
│   └── processed/.gitkeep
├── notebooks/.gitkeep
├── src/cs703/
│   ├── __init__.py
│   ├── config.py
│   └── data/__init__.py
└── tests/__init__.py
```

- `data/raw`、`data/interim`、`data/processed`：分別放原始下載、清理中、最終可建模的資料。三者皆加進 `.gitignore`（用 `.gitkeep` 保留空目錄結構）。
- `notebooks/`：之後放 EDA 與建模 notebook，本次只留空目錄。
- `src/cs703/config.py`：用 `python-dotenv` 讀取 `.env`，定義 `DATA_RAW_DIR`、`DATA_INTERIM_DIR`、`DATA_PROCESSED_DIR` 等路徑常數，以及之後會用到的 API 金鑰讀取（`SOCRATA_APP_TOKEN`、`TICKETMASTER_API_KEY`）。
- `src/cs703/data/__init__.py`：先留空，之後才放各資料來源的抓取腳本（violations、meters、weather、events 等）。
- `tests/`：先建好目錄與 `__init__.py`，暫不寫測試案例。

## 依賴套件

透過 `uv add` 安裝：`pandas`、`numpy`、`scikit-learn`、`xgboost`、`geopandas`、`matplotlib`、`seaborn`、`jupyter`、`python-dotenv`、`requests`、`sodapy`（NYC Open Data / Socrata 官方 client）。

## 文件轉換

把下列兩份 docx 轉成 Markdown 放進 `docs/`（用 `textutil` 轉純文字後，人工整理成結構化 Markdown，保留原始章節與表格內容）：

- `CS703_Phase1_Business_Understanding.docx` → `docs/phase1-business-understanding.md`
- `Data_Science_Project_Proposal_Parking_NYC.docx` → `docs/project-proposal.md`

原始 docx/pdf 檔案留在 Desktop 資料夾不動，repo 裡只放 Markdown 版本。

## .env 與金鑰管理

- `.env.example`：列出欄位名稱但不含真實值（`SOCRATA_APP_TOKEN=`、`TICKETMASTER_API_KEY=`）。
- `.env`：加進 `.gitignore`，不進版本控制。
- `src/cs703/config.py` 用 `python-dotenv` 的 `load_dotenv()` 讀取。

## README 內容

簡短說明專案主題（一句話）、CRISP-DM 六階段目前進度（目前完成 Phase 1，Phase 2 進行中）、如何用 `uv sync` 設定環境、目錄結構說明。

## 明確排除範圍

- 不寫任何實際資料抓取程式碼（Phase 2 的爬蟲/API client）。
- 不建立 CI/CD 設定。
- 不寫測試案例內容（只建空的 `tests/__init__.py`）。
- 不收錄 `Project_Proposal.docx`（舊構想，方向不一致）。
