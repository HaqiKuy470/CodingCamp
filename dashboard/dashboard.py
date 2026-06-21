import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Bike Sharing Dashboard", page_icon="🚲", layout="wide")

# ── Load & prep data ──────────────────────────────────────────
@st.cache_data
def load_data():
    df_hour = pd.read_csv('dashboard/main_data.csv')
    df_hour['dteday'] = pd.to_datetime(df_hour['dteday'])
    season_map  = {1:'Spring',2:'Summer',3:'Fall',4:'Winter'}
    weather_map = {1:'Clear',2:'Mist/Cloudy',3:'Light Rain/Snow',4:'Heavy Rain'}
    weekday_map = {0:'Senin',1:'Selasa',2:'Rabu',3:'Kamis',4:'Jumat',5:'Sabtu',6:'Minggu'}
    df_hour['season_name']  = df_hour['season'].map(season_map)
    df_hour['weather_name'] = df_hour['weathersit'].map(weather_map)
    df_hour['weekday_name'] = df_hour['weekday'].map(weekday_map)

    # Clustering
    hourly_avg = df_hour.groupby('hr')['cnt'].mean()
    def cluster_jam(cnt):
        if cnt < 50:    return 'Very Low'
        elif cnt < 100: return 'Low'
        elif cnt < 220: return 'Medium'
        elif cnt < 350: return 'High'
        else:           return 'Very High'
    hc = hourly_avg.apply(cluster_jam).reset_index()
    hc.columns = ['hr','intensity_cluster']
    df_hour = df_hour.merge(hc, on='hr')

    def cluster_hari(row):
        if row['weekday'] >= 5:                return 'Weekend'
        elif row['hr'] in [7,8,9,16,17,18,19]: return 'Workday Peak'
        else:                                   return 'Workday Normal'
    df_hour['day_segment'] = df_hour.apply(cluster_hari, axis=1)

    def cluster_kondisi(row):
        if row['season'] in [2,3] and row['weathersit'] in [1,2]: return 'Kondisi Ideal'
        elif row['weathersit'] >= 3 or row['season'] == 1:         return 'Kondisi Buruk'
        else:                                                        return 'Kondisi Sedang'
    df_hour['condition_cluster'] = df_hour.apply(cluster_kondisi, axis=1)
    return df_hour

df = load_data()

COLOR = {
    'Very Low':'#3a4a6b','Low':'#4e7fba','Medium':'#f0a500','High':'#e05c3a','Very High':'#c0392b',
    'Workday Peak':'#e74c3c','Workday Normal':'#27ae60','Weekend':'#9b59b6',
    'Kondisi Ideal':'#27ae60','Kondisi Sedang':'#f39c12','Kondisi Buruk':'#e74c3c',
}
CLUSTER_ORDER = ['Very Low','Low','Medium','High','Very High']

# ── Header ────────────────────────────────────────────────────
st.title("🚲 Bike Sharing Dashboard")
st.caption("Analisis Data Capital Bikeshare System, Washington D.C. (2011–2012)")

# ── Sidebar filter ────────────────────────────────────────────
st.sidebar.header("Filter Data")
year_opt = st.sidebar.multiselect("Tahun", [2011, 2012],
    default=[2011, 2012], format_func=lambda x: str(x))
season_opt = st.sidebar.multiselect("Musim", ['Spring','Summer','Fall','Winter'],
    default=['Spring','Summer','Fall','Winter'])

filtered = df[
    (df['yr'].map({0:2011,1:2012}).isin(year_opt)) &
    (df['season_name'].isin(season_opt))
]

# ── KPI Metrics ───────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Penyewaan",    f"{filtered['cnt'].sum():,.0f}")
col2.metric("Rata-rata per Jam",  f"{filtered['cnt'].mean():.1f}")
col3.metric("Tertinggi",          f"{filtered['cnt'].max():,}")
col4.metric("Total Registered",   f"{filtered['registered'].sum():,.0f}")

st.divider()

# ── Tab layout ────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📈 Pola Penyewaan", "🌤️ Cuaca & Musim", "🔵 Clustering"])

with tab1:
    st.subheader("Pola Penyewaan per Jam: Hari Kerja vs Akhir Pekan")
    hw = filtered[filtered['workingday']==1].groupby('hr')['cnt'].mean()
    we = filtered[filtered['workingday']==0].groupby('hr')['cnt'].mean()
    fig, ax = plt.subplots(figsize=(12,4))
    ax.plot(hw.index, hw.values, 'o-', color='#2ecc71', lw=2.5, ms=5, label='Hari Kerja')
    ax.plot(we.index, we.values, 's--', color='#9b59b6', lw=2.5, ms=5, label='Akhir Pekan')
    ax.set_xlabel('Jam'); ax.set_ylabel('Rata-rata Penyewaan')
    ax.set_xticks(range(24)); ax.legend(); ax.grid(alpha=0.3)
    st.pyplot(fig); plt.close()

    st.subheader("Heatmap Penyewaan: Jam × Hari")
    pivot = filtered.groupby(['hr','weekday'])['cnt'].mean().unstack()
    pivot.columns = ['Sen','Sel','Rab','Kam','Jum','Sab','Min']
    fig, ax = plt.subplots(figsize=(12,4))
    sns.heatmap(pivot.T, cmap='YlOrRd', linewidths=0.3, ax=ax,
                cbar_kws={'label':'Avg cnt','shrink':0.85})
    ax.set_xlabel('Jam (0-23)'); ax.set_ylabel('Hari')
    st.pyplot(fig); plt.close()

with tab2:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Penyewaan per Musim")
        season_order  = ['Spring','Summer','Fall','Winter']
        season_colors = ['#3498db','#f39c12','#e74c3c','#9b59b6']
        sm = filtered.groupby('season_name')['cnt'].mean().reindex(season_order)
        fig, ax = plt.subplots(figsize=(6,4))
        bars = ax.bar(season_order, sm.values, color=season_colors, alpha=0.85, width=0.6)
        for bar, val in zip(bars, sm.values):
            ax.text(bar.get_x()+bar.get_width()/2, val+2, f'{val:.0f}', ha='center', fontweight='bold')
        ax.set_ylabel('Rata-rata cnt'); ax.grid(axis='y', alpha=0.4)
        st.pyplot(fig); plt.close()
    with c2:
        st.subheader("Penyewaan per Cuaca")
        wm = filtered.groupby('weather_name')['cnt'].mean()
        weather_order = ['Clear','Mist/Cloudy','Light Rain/Snow','Heavy Rain']
        avail = [w for w in weather_order if w in wm.index]
        wm = wm.reindex(avail)
        fig, ax = plt.subplots(figsize=(6,4))
        bars = ax.bar(range(len(wm)), wm.values, color=['#27ae60','#f39c12','#3498db','#e74c3c'][:len(wm)], alpha=0.85, width=0.55)
        ax.set_xticks(range(len(wm))); ax.set_xticklabels(wm.index, rotation=10, ha='right')
        for bar, val in zip(bars, wm.values):
            ax.text(bar.get_x()+bar.get_width()/2, val+2, f'{val:.0f}', ha='center', fontweight='bold')
        ax.set_ylabel('Rata-rata cnt'); ax.grid(axis='y', alpha=0.4)
        st.pyplot(fig); plt.close()

with tab3:
    st.subheader("Clustering 1: Intensitas Jam")
    hourly_avg = filtered.groupby('hr')['cnt'].mean()
    hc = filtered.groupby('hr')['intensity_cluster'].first().reset_index()
    fig, axes = plt.subplots(1,2, figsize=(14,4))
    hrs    = hc['hr'].values
    avgs   = [hourly_avg[h] for h in hrs]
    colors = [COLOR[c] for c in hc['intensity_cluster']]
    axes[0].bar(hrs, avgs, color=colors, width=0.75, alpha=0.88)
    axes[0].set_xticks(range(0,24,2)); axes[0].set_xlabel('Jam'); axes[0].set_ylabel('Rata-rata cnt')
    axes[0].set_title('Intensitas per Jam', fontweight='bold')
    patches = [mpatches.Patch(color=COLOR[c], label=c) for c in CLUSTER_ORDER]
    axes[0].legend(handles=patches, fontsize=8)
    seg_mean = filtered.groupby('day_segment')['cnt'].mean()
    seg_order = ['Workday Normal','Weekend','Workday Peak']
    seg_mean = seg_mean.reindex([s for s in seg_order if s in seg_mean.index])
    bars = axes[1].barh(seg_mean.index, seg_mean.values, color=[COLOR[s] for s in seg_mean.index], height=0.45, alpha=0.88)
    for bar, val in zip(bars, seg_mean.values):
        axes[1].text(val+2, bar.get_y()+bar.get_height()/2, f'{val:.0f}', va='center', fontweight='bold')
    axes[1].set_xlabel('Rata-rata cnt'); axes[1].set_title('Segmentasi Hari', fontweight='bold')
    plt.tight_layout(); st.pyplot(fig); plt.close()

    st.subheader("Clustering 3: Kondisi Operasional")
    cond_order = ['Kondisi Ideal','Kondisi Sedang','Kondisi Buruk']
    cond_mean  = filtered.groupby('condition_cluster')['cnt'].mean().reindex(cond_order)
    fig, ax = plt.subplots(figsize=(7,4))
    bars = ax.bar(['Ideal','Sedang','Buruk'], cond_mean.values,
                  color=[COLOR[c] for c in cond_order], width=0.5, alpha=0.88)
    for bar, val in zip(bars, cond_mean.values):
        ax.text(bar.get_x()+bar.get_width()/2, val+2, f'{val:.0f}', ha='center', fontweight='bold')
    ax.set_ylabel('Rata-rata cnt'); ax.grid(axis='y', alpha=0.4)
    ax.set_title('Rata-rata Penyewaan per Kluster Kondisi', fontweight='bold')
    st.pyplot(fig); plt.close()

st.sidebar.divider()
st.sidebar.info("Proyek Analisis Data — Dicoding 2024")
