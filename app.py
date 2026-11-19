import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="候鳥遷徙動態儀表板", layout="wide")
st.title("🌍 全球候鳥遷徙動態追蹤儀表板")
st.markdown("💡 **視覺化指南**：不同顏色代表不同物種；**實線**代表遷徙成功，**虛線**代表遷徙失敗或中斷。點擊地圖下方的 **Play** 按鈕可觀看動態飛行實況。")

# ==========================================
# 1. 載入真實資料
# ==========================================
@st.cache_data
def load_data():
    # 讀取你指定的本地端 Kaggle CSV 檔案
    df = pd.read_csv(r"C:\Users\turtlepeer\project1\TA_project\final_demo_115a\bird_migration_with_origin_destination.csv") 
    
    # 清理可能有空值的座標與必要欄位，避免畫圖報錯
    df = df.dropna(subset=['Start_Latitude', 'Start_Longitude', 'End_Latitude', 'End_Longitude', 'Species'])
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("找不到 CSV 檔案，請確認檔案路徑是否正確。")
    st.stop()

unique_species = df['Species'].unique()
color_palette = px.colors.qualitative.Plotly 
colors = {species: color_palette[i % len(color_palette)] for i, species in enumerate(unique_species)}

# ==========================================
# 2. 軌跡內插演算法 (Trajectory Interpolation)
# ==========================================
@st.cache_data
def generate_animation_frames(df_subset, steps=15):
    """將起訖點切分為多個 Frame，製造飛行過程的動畫資料"""
    frames = []
    for _, row in df_subset.iterrows():
        # 利用線性內插產生中間虛擬座標點
        lats = np.linspace(row['Start_Latitude'], row['End_Latitude'], steps)
        lons = np.linspace(row['Start_Longitude'], row['End_Longitude'], steps)
        
        for step in range(steps):
            frame_data = row.copy()
            frame_data['Current_Lat'] = lats[step]
            frame_data['Current_Lon'] = lons[step]
            frame_data['Step'] = step
            frames.append(frame_data)
            
    return pd.DataFrame(frames)

# ==========================================
# 3. 側邊欄：進階互動控制面板
# ==========================================
st.sidebar.header("🔍 篩選與顯示設定")

selected_species = st.sidebar.multiselect(
    "1. 選擇鳥類物種 (Species):",
    options=unique_species,
    default=unique_species[:3] # 預設少一點，讓動畫跑得順
)

success_options = df['Migration_Success'].dropna().unique()
selected_success = st.sidebar.multiselect(
    "2. 遷徙狀態 (Migration_Success):",
    options=success_options,
    default=success_options
)

# 如果資料有天氣欄位，加入天氣篩選器加強聯動性
if 'Weather_Condition' in df.columns:
    weather_options = df['Weather_Condition'].dropna().unique()
    selected_weather = st.sidebar.multiselect(
        "3. 遭遇天氣條件:",
        options=weather_options,
        default=weather_options
    )
else:
    selected_weather = []

map_style = st.sidebar.radio(
    "4. 選擇地圖視角 (Map Projection):",
    options=["2D 平面地圖 (Natural Earth)", "3D 立體地球 (Orthographic)"],
    index=0 
)

projection_mapping = {
    "2D 平面地圖 (Natural Earth)": "natural earth", 
    "3D 立體地球 (Orthographic)": "orthographic"
}
selected_projection = projection_mapping[map_style]

# 套用篩選邏輯
filtered_df = df[
    (df['Species'].isin(selected_species)) & 
    (df['Migration_Success'].isin(selected_success))
]
if 'Weather_Condition' in df.columns and selected_weather:
    filtered_df = filtered_df[filtered_df['Weather_Condition'].isin(selected_weather)]

max_available = len(filtered_df) if len(filtered_df) > 0 else 1
display_count = st.sidebar.slider(
    "5. 顯示路線數量上限 (控制動畫效能):",
    min_value=1,
    max_value=max_available,
    value=min(30, max_available) 
)

display_df = filtered_df.head(display_count)
st.sidebar.write(f"目前渲染數量: **{len(display_df)}** 筆 (總符合: {len(filtered_df)} 筆)")

# ==========================================
# 4. [新功能] 多圖表聯動分析 (Cross-filtering)
# ==========================================
if not display_df.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 平均飛行距離")
        if 'Flight_Distance_km' in display_df.columns:
            dist_df = display_df.groupby('Species')['Flight_Distance_km'].mean().reset_index()
            fig_bar = px.bar(dist_df, x='Species', y='Flight_Distance_km', color='Species',
                             color_discrete_map=colors, text_auto='.0f')
            fig_bar.update_layout(showlegend=False, height=300, margin=dict(t=30, b=0, l=0, r=0))
            st.plotly_chart(fig_bar, use_container_width=True)
            
    with col2:
        st.subheader("🌤️ 氣候條件分佈")
        if 'Weather_Condition' in display_df.columns:
            weather_df = display_df['Weather_Condition'].value_counts().reset_index()
            weather_df.columns = ['Weather_Condition', 'Count']
            fig_pie = px.pie(weather_df, names='Weather_Condition', values='Count', hole=0.4)
            fig_pie.update_layout(height=300, margin=dict(t=30, b=0, l=0, r=0))
            st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")

# ==========================================
# 5. [新功能] 動態內插地圖 (Animated Trajectories)
# ==========================================
st.subheader("🗺️ 動態飛行追蹤地圖")

if not display_df.empty:
    # 產生動畫所需的中間影格資料
    anim_df = generate_animation_frames(display_df, steps=15)
    
    # 建立動態散佈圖 (會自動生成下方的播放時間軸)
    fig = px.scatter_geo(
        anim_df,
        lat="Current_Lat", lon="Current_Lon",
        color="Species", color_discrete_map=colors,
        animation_frame="Step",
        hover_name="Bird_ID" if 'Bird_ID' in anim_df.columns else "Species",
        size_max=8,
        projection=selected_projection
    )
    
    # 將動態點的透明度拉高
    fig.update_traces(marker=dict(size=6, opacity=1.0, line=dict(width=1, color='white')))

    # 疊加原始的「起訖靜態連線」，讓軌跡具備方向感
    for _, row in display_df.iterrows():
        color = colors.get(row['Species'], 'gray') 
        is_success = str(row.get('Migration_Success', 'Yes')) == 'Yes' 
        line_dash = 'solid' if is_success else 'dash'
        
        # 使用 add_trace 把靜態線條加進動畫地圖的背景
        fig.add_trace(go.Scattergeo(
            lon=[row['Start_Longitude'], row['End_Longitude']],
            lat=[row['Start_Latitude'], row['End_Latitude']],
            mode='lines',
            line=dict(width=1, color=color, dash=line_dash),
            opacity=0.3, # 背景線調淡
            showlegend=False,
            hoverinfo='skip'
        ))

    # 更新地球外觀
    fig.update_geos(
        showcoastlines=True, coastlinecolor="RebeccaPurple",
        showland=True, landcolor="LightGreen",
        showocean=True, oceancolor="Azure",
        lataxis_showgrid=True, lonaxis_showgrid=True,
        showcountries=True
    )
    fig.update_layout(height=700, margin={"r":0,"t":0,"l":0,"b":0})
    
    # 將動畫速度調快，體驗更好
    fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 150
    fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 100

    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ==========================================
# 6. [新功能] 飛行高度剖面圖 (Altitude Profile)
# ==========================================
st.subheader("🏔️ 特定個體飛行高度剖面圖")

if not display_df.empty and 'Max_Altitude_m' in display_df.columns and 'Min_Altitude_m' in display_df.columns:
    col_sel, col_chart = st.columns([1, 3])
    
    with col_sel:
        st.write("選擇要深度觀察的個體：")
        bird_id_col = 'Bird_ID' if 'Bird_ID' in display_df.columns else display_df.index
        selected_bird = st.selectbox("選擇 ID:", display_df[bird_id_col])
        
    with col_chart:
        # 取出該隻鳥的高度資料
        if 'Bird_ID' in display_df.columns:
            bird_data = display_df[display_df['Bird_ID'] == selected_bird].iloc[0]
        else:
            bird_data = display_df.loc[selected_bird]
            
        max_alt = bird_data['Max_Altitude_m']
        min_alt = bird_data['Min_Altitude_m']
        
        # 用數學拋物線公式模擬飛行高度起伏 (起飛 -> 爬升至最高 -> 降落)
        x_steps = np.linspace(0, 100, 50) 
        y_alts = -4 * (max_alt - min_alt) * ((x_steps/100 - 0.5)**2) + max_alt
        y_alts = np.maximum(y_alts, min_alt) 
        
        fig_alt = px.area(
            x=x_steps, y=y_alts, 
            labels={'x': '航程進度 (%)', 'y': '飛行海拔高度 (公尺)'},
            title=f"物種: {bird_data['Species']} | 最高海拔: {max_alt}m"
        )
        bird_color = colors.get(bird_data['Species'], 'blue')
        fig_alt.update_traces(line_color=bird_color, fillcolor=bird_color, opacity=0.4)
        fig_alt.update_layout(height=250, margin=dict(t=40, b=10, l=10, r=10))
        st.plotly_chart(fig_alt, use_container_width=True)
else:
    st.info("⚠️ 找不到 'Max_Altitude_m' 與 'Min_Altitude_m' 欄位，無法繪製高度剖面圖。")

with st.expander("📄 查看目前地圖上顯示的原始資料表"):
    st.dataframe(display_df, use_container_width=True)