import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Bike Sharing Dashboard",
    page_icon="🚲",
    layout="wide"
)

@st.cache_data
def load_data():
    df = pd.read_csv('dashboard/main_data.csv')
    df['dteday'] = pd.to_datetime(df['dteday'])
    season_map  = {1:'Spring',2:'Summer',3:'Fall',4:'Winter'}
    weather_map = {1:'Clear',2:'Mist/Cloudy',3:'Light Rain/Snow',4:'Heavy Rain'}
    df['season_name']  = df['season'].map(season_map)
    df['weather_name'] = df['weathersit'].map(weather_map)

    # Clustering
    hourly_avg = df.groupby('hr')['cnt'].mean()
    def cluster_jam(cnt):
        if cnt < 50:    return 'Very Low'
        elif cnt < 100: return 'Low'
        elif cnt < 220: return 'Medium'
        elif cnt < 350: return 'High'
        else:           return 'Very High'
    hc = hourly_avg.apply(cluster_jam).reset_index()
    hc.columns = ['hr','intensity_cluster']
    df = df.merge(hc, on='hr')

    def cluster_hari(row):
        if row['weekday'] >= 5:                return 'Weekend'
        elif row['hr'] in [7,8,9,16,17,18,19]: return 'Workday Peak'
        else:                                   return 'Workday Normal'
    df['day_segment'] = df.apply(cluster_hari, axis=1)

    def cluster_kondisi(row):
        if row['season'] in [2,3] and row['weathersit'] in [1,2]: return 'Kondisi Ideal'
        elif row['weathersit'] >= 3 or row['season'] == 1:         return 'Kondisi Buruk'
        else:                                                        return 'Kondisi Sedang'
    df['condition_cluster'] = df.apply(cluster_kondisi, axis=1)
    return df

df = load_data()

# ── Header ────────────────────────────────────────────────────
st.title("🚲 Bike Sharing Dashboard")
st.caption("Analisis Data Capital Bikeshare System, Washington D.C. (2011–2012)")
st.markdown("""
**Pertanyaan Bisnis:**
1. *Pada jam berapa saja terjadi puncak penyewaan sepeda selama periode 2011–2012, dan bagaimana perbedaan polanya antara hari kerja dan akhir pekan?*
2. *Bagaimana perbedaan rata-rata jumlah penyewaan sepeda pada setiap kondisi cuaca dan musim selama periode 2011–2012?*
""")

# ── Sidebar filter ────────────────────────────────────────────
st.sidebar.header("🔍 Filter Data")
year_opt = st.sidebar.multiselect(
    "Tahun", [2011, 2012], default=[2011, 2012],
    format_func=lambda x: str(x)
)
season_opt = st.sidebar.multiselect(
    "Musim", ['Spring','Summer','Fall','Winter'],
    default=['Spring','Summer','Fall','Winter']
)
day_type = st.sidebar.radio(
    "Tipe Hari", ["Semua", "Hari Kerja", "Akhir Pekan"]
)

filtered = df[
    (df['yr'].map({0:2011,1:2012}).isin(year_opt)) &
    (df['season_name'].isin(season_opt))
]
if day_type == "Hari Kerja":
    filtered = filtered[filtered['workingday'] == 1]
elif day_type == "Akhir Pekan":
    filtered = filtered[filtered['workingday'] == 0]

# ── KPI ───────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Penyewaan",   f"{filtered['cnt'].sum():,.0f}")
c2.metric("Rata-rata/Jam",     f"{filtered['cnt'].mean():.1f}")
c3.metric("Puncak Tertinggi",  f"{filtered['cnt'].max():,}")
c4.metric("Total Registered",  f"{filtered['registered'].sum():,.0f}")
st.divider()

# ── Tab ───────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "📈 Pertanyaan 1: Pola Jam",
    "🌤️ Pertanyaan 2: Cuaca & Musim",
    "🔵 Clustering Lanjutan"
])

with tab1:
    st.subheader("Pola Penyewaan per Jam: Hari Kerja vs Akhir Pekan (2011–2012)")
    st.caption("Menjawab: *Pada jam berapa puncak penyewaan terjadi dan bagaimana pola berbeda antara hari kerja dan akhir pekan?*")

    hw = filtered[filtered['workingday']==1].groupby('hr')['cnt'].mean()
    we = filtered[filtered['workingday']==0].groupby('hr')['cnt'].mean()

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(hw.index, hw.values, 'o-', color='#2ecc71', lw=2.5, ms=5, label='Hari Kerja')
    ax.plot(we.index, we.values, 's--', color='#9b59b6', lw=2.5, ms=5, label='Akhir Pekan')
    if not hw.empty:
        pk = hw.idxmax()
        ax.annotate(f'Puncak\nJam {pk}: {hw[pk]:.0f}', xy=(pk, hw[pk]),
                    xytext=(pk+1.5, hw[pk]+30), fontsize=9, color='#2ecc71',
                    arrowprops=dict(arrowstyle='->', color='#2ecc71'))
    if not we.empty:
        pk2 = we.idxmax()
        ax.annotate(f'Puncak\nJam {pk2}: {we[pk2]:.0f}', xy=(pk2, we[pk2]),
                    xytext=(pk2-5, we[pk2]+30), fontsize=9, color='#9b59b6',
                    arrowprops=dict(arrowstyle='->', color='#9b59b6'))
    ax.set_xlabel('Jam'); ax.set_ylabel('Rata-rata Penyewaan')
    ax.set_xticks(range(24)); ax.legend(); ax.grid(alpha=0.3)
    st.pyplot(fig); plt.close()

    st.subheader("Heatmap Penyewaan: Jam × Hari")
    pivot = filtered.groupby(['hr','weekday'])['cnt'].mean().unstack()
    pivot.columns = ['Sen','Sel','Rab','Kam','Jum','Sab','Min']
    fig, ax = plt.subplots(figsize=(12, 4))
    sns.heatmap(pivot.T, cmap='YlOrRd', linewidths=0.3, ax=ax,
                cbar_kws={'label':'Rata-rata cnt', 'shrink': 0.85})
    ax.set_xlabel('Jam (0–23)'); ax.set_ylabel('Hari')
    st.pyplot(fig); plt.close()

    # Ringkasan insight
    if not hw.empty and not we.empty:
        st.info(
            f"💡 **Insight**: Puncak hari kerja terjadi pada **jam {hw.idxmax():02d}:00** "
            f"({hw.max():.0f}/jam) dan akhir pekan pada **jam {we.idxmax():02d}:00** "
            f"({we.max():.0f}/jam). Hari kerja menunjukkan pola bimodal (pagi & sore) "
            "khas komuter, sedangkan akhir pekan unimodal (siang hari)."
        )

with tab2:
    st.subheader("Pengaruh Kondisi Cuaca & Musim terhadap Penyewaan (2011–2012)")
    st.caption("Menjawab: *Bagaimana perbedaan rata-rata penyewaan pada setiap kondisi cuaca dan musim?*")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Per Musim**")
        season_order  = ['Spring','Summer','Fall','Winter']
        season_colors = ['#3498db','#f39c12','#e74c3c','#9b59b6']
        sm = filtered.groupby('season_name')['cnt'].mean().reindex(
            [s for s in season_order if s in filtered['season_name'].unique()])
        fig, ax = plt.subplots(figsize=(6, 4))
        bars = ax.bar(sm.index, sm.values,
                      color=[season_colors[season_order.index(s)] for s in sm.index],
                      alpha=0.85, width=0.6)
        ax.set_ylabel('Rata-rata cnt'); ax.grid(axis='y', alpha=0.4)
        for bar, val in zip(bars, sm.values):
            ax.text(bar.get_x()+bar.get_width()/2, val+2,
                    f'{val:.0f}', ha='center', fontweight='bold')
        st.pyplot(fig); plt.close()

    with c2:
        st.markdown("**Per Kondisi Cuaca**")
        weather_order  = ['Clear','Mist/Cloudy','Light Rain/Snow']
        weather_colors = ['#27ae60','#f39c12','#3498db']
        avail_w = [w for w in weather_order if w in filtered['weather_name'].unique()]
        wm = filtered.groupby('weather_name')['cnt'].mean().reindex(avail_w)
        fig, ax = plt.subplots(figsize=(6, 4))
        bars = ax.bar(range(len(wm)), wm.values,
                      color=[weather_colors[weather_order.index(w)] for w in wm.index],
                      alpha=0.85, width=0.55)
        ax.set_xticks(range(len(wm)))
        ax.set_xticklabels(wm.index, rotation=10, ha='right')
        ax.set_ylabel('Rata-rata cnt'); ax.grid(axis='y', alpha=0.4)
        for bar, val in zip(bars, wm.values):
            ax.text(bar.get_x()+bar.get_width()/2, val+2,
                    f'{val:.0f}', ha='center', fontweight='bold')
        st.pyplot(fig); plt.close()

    # Insight cuaca
    if 'Clear' in filtered['weather_name'].unique() and 'Light Rain/Snow' in filtered['weather_name'].unique():
        clear = filtered[filtered['weather_name']=='Clear']['cnt'].mean()
        rain  = filtered[filtered['weather_name']=='Light Rain/Snow']['cnt'].mean()
        st.warning(
            f"⚠️ **Insight**: Penyewaan saat cuaca cerah rata-rata **{clear:.0f}/jam**, "
            f"turun **{(1-rain/clear)*100:.0f}%** menjadi **{rain:.0f}/jam** saat hujan/salju. "
            "Kondisi cuaca memberikan dampak signifikan terhadap demand."
        )

    st.subheader("Tren Penyewaan Bulanan per Musim")
    monthly = filtered.copy()
    monthly['yearmonth'] = monthly['dteday'].dt.to_period('M').astype(str)
    monthly_mean = monthly.groupby(['yearmonth','season_name'])['cnt'].mean().reset_index()
    fig, ax = plt.subplots(figsize=(12, 4))
    for season, color in zip(season_order, season_colors):
        sub = monthly_mean[monthly_mean['season_name']==season]
        if not sub.empty:
            ax.plot(sub['yearmonth'], sub['cnt'], 'o-', color=color, lw=2, label=season, ms=5)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right', fontsize=8)
    ax.set_ylabel('Rata-rata cnt/jam'); ax.legend(); ax.grid(alpha=0.3)
    ax.set_title('Tren Rata-rata Penyewaan per Bulan & Musim (2011–2012)', fontweight='bold')
    plt.tight_layout()
    st.pyplot(fig); plt.close()

with tab3:
    st.subheader("Clustering Manual Grouping (Analisis Lanjutan)")

    COLOR = {
        'Very Low':'#3a4a6b','Low':'#4e7fba','Medium':'#f0a500',
        'High':'#e05c3a','Very High':'#c0392b',
        'Workday Peak':'#e74c3c','Workday Normal':'#27ae60','Weekend':'#9b59b6',
        'Kondisi Ideal':'#27ae60','Kondisi Sedang':'#f39c12','Kondisi Buruk':'#e74c3c',
    }
    CLUSTER_ORDER = ['Very Low','Low','Medium','High','Very High']

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Cluster 1: Intensitas Jam**")
        hourly_avg = filtered.groupby('hr')['cnt'].mean()
        hc = filtered.groupby('hr')['intensity_cluster'].first().reset_index()
        fig, ax = plt.subplots(figsize=(7, 4))
        hrs    = hc['hr'].values
        avgs   = [hourly_avg.get(h, 0) for h in hrs]
        colors = [COLOR[c] for c in hc['intensity_cluster']]
        ax.bar(hrs, avgs, color=colors, width=0.75, alpha=0.88)
        ax.set_xticks(range(0,24,2))
        ax.set_xlabel('Jam'); ax.set_ylabel('Rata-rata cnt')
        patches = [mpatches.Patch(color=COLOR[c], label=c) for c in CLUSTER_ORDER]
        ax.legend(handles=patches, fontsize=7)
        st.pyplot(fig); plt.close()

    with col2:
        st.markdown("**Cluster 2: Segmentasi Hari**")
        seg_order = ['Workday Normal','Weekend','Workday Peak']
        seg_mean  = filtered.groupby('day_segment')['cnt'].mean().reindex(
            [s for s in seg_order if s in filtered['day_segment'].unique()])
        fig, ax = plt.subplots(figsize=(7, 4))
        bars = ax.barh(seg_mean.index, seg_mean.values,
                       color=[COLOR[s] for s in seg_mean.index],
                       height=0.45, alpha=0.88)
        for bar, val in zip(bars, seg_mean.values):
            ax.text(val+2, bar.get_y()+bar.get_height()/2,
                    f'{val:.0f}', va='center', fontweight='bold')
        ax.set_xlabel('Rata-rata cnt')
        st.pyplot(fig); plt.close()

    st.markdown("**Cluster 3: Kondisi Operasional (Cuaca + Musim)**")
    cond_order = ['Kondisi Ideal','Kondisi Sedang','Kondisi Buruk']
    cond_mean  = filtered.groupby('condition_cluster')['cnt'].mean().reindex(
        [c for c in cond_order if c in filtered['condition_cluster'].unique()])
    fig, ax = plt.subplots(figsize=(8, 3))
    bars = ax.bar(['Ideal','Sedang','Buruk'][:len(cond_mean)],
                  cond_mean.values,
                  color=[COLOR[c] for c in cond_mean.index],
                  width=0.5, alpha=0.88)
    for bar, val in zip(bars, cond_mean.values):
        ax.text(bar.get_x()+bar.get_width()/2, val+2,
                f'{val:.0f}', ha='center', fontweight='bold')
    ax.set_ylabel('Rata-rata cnt'); ax.grid(axis='y', alpha=0.4)
    plt.tight_layout()
    st.pyplot(fig); plt.close()

st.sidebar.divider()
st.sidebar.success("✅ Data: 2011–2012")
st.sidebar.info("Proyek Analisis Data — Dicoding")
