# Proyek Analisis Data: Bike Sharing Dataset

## Deskripsi Proyek
Proyek analisis data menggunakan **Bike Sharing Dataset** dari Capital Bikeshare System, Washington D.C. (2011–2012). Proyek ini mencakup analisis eksplorasi data, visualisasi, dan teknik clustering manual grouping.

## Pertanyaan Bisnis
1. Pada jam berapa saja terjadi puncak penyewaan sepeda, dan bagaimana polanya berbeda antara hari kerja dan akhir pekan?
2. Bagaimana pengaruh kondisi cuaca dan musim terhadap jumlah penyewaan sepeda?

## Struktur Direktori
```
submission/
├── dashboard/
│   ├── main_data.csv
│   └── dashboard.py
├── data/
│   ├── hour.csv
│   └── day.csv
├── notebook.ipynb
├── README.md
├── requirements.txt
└── url.txt
```

## Setup Environment

### Menggunakan pip
```bash
pip install -r requirements.txt
```

### Menggunakan conda
```bash
conda create --name bike-sharing python=3.11
conda activate bike-sharing
pip install -r requirements.txt
```

## Menjalankan Dashboard

```bash
cd submission
streamlit run dashboard/dashboard.py
```

Dashboard akan terbuka di browser pada `http://localhost:8501`

## Dataset
- **Sumber**: [UCI Machine Learning Repository](https://archive.ics.uci.edu/ml/datasets/bike+sharing+dataset)
- `hour.csv`: 17.379 records data per jam (2011–2012)
- `day.csv`: 731 records data per hari (2011–2012)

## Teknik Analisis
- Gathering, Assessing, dan Cleaning Data
- Exploratory Data Analysis (EDA)
- Visualisasi (line chart, box plot, heatmap, bar chart)
- **Clustering Manual Grouping** (teknik analisis lanjutan):
  - Clustering Intensitas Jam (5 tier)
  - Clustering Segmentasi Hari (3 tier)
  - Clustering Kondisi Operasional (3 tier)
