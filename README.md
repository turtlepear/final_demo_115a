# 全球候鳥遷徙動態儀表板（final_demo_115a）

用 **Streamlit + Plotly** 做的互動式儀表板，把候鳥遷徙資料畫在世界地圖上，並用動畫呈現飛行過程。

## 功能

- **篩選面板**：依物種、遷徙是否成功、天氣條件篩選，可限制顯示的路線數量。
- **2D / 3D 地圖切換**：Natural Earth 平面地圖或 Orthographic 立體地球。
- **動態飛行軌跡**：用線性內插把起點到終點切成多個影格，按 Play 播放飛行動畫；實線代表遷徙成功，虛線代表失敗或中斷。
- **統計圖表**：各物種平均飛行距離（長條圖）、天氣條件分布（圓餅圖）。
- **飛行高度剖面**：選一隻鳥，用拋物線模擬起飛、爬升到最高點、降落的高度變化。
- **原始資料表**：查看目前地圖上顯示的資料。

## 檔案說明

| 檔案 | 說明 |
| --- | --- |
| `app.py` | Streamlit 儀表板主程式 |
| `bird_migration_data.csv` | 原始候鳥遷徙資料（Kaggle） |
| `Bird_Migration_Data_with_Origin.csv` | 加上 `Origin`（起點座標）欄位 |
| `bird_migration_with_origin_destination.csv` | 加上 `Origin` 與 `Destination` 欄位，`app.py` 使用這份 |

## 環境需求

```bash
pip install streamlit pandas numpy plotly
```

## 使用方式

> `app.py` 讀取 CSV 用的是寫死的絕對路徑，執行前請先改成自己電腦上的路徑（例如 `bird_migration_with_origin_destination.csv`）。

```bash
streamlit run app.py
```

執行後瀏覽器會自動開啟儀表板（預設 http://localhost:8501）。
