import streamlit as st
import pandas as pd
import plotly.express as px

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="KSO SCISI - Customer Dashboard",
    page_icon="📊",
    layout="wide"
)

# ==========================================
# 📝 DEFINISI SEGMEN & STRATEGI
# ==========================================
# Ini adalah "Kamus" untuk dashboard Anda
SEGMENT_INFO = {
    "Champions": {
        "desc": "R=4, F=4, M=4. Baru saja beli, sering beli, dan nilai transaksinya besar.",
        "action": "💎 **Prioritas Utama Retensi.** Berikan layanan VIP, reward, dan akses eksklusif. Jangan sampai lepas.",
        "color": "#1a9850" # Hijau Tua
    },
    "Loyal Customers": {
        "desc": "R=3/4, F=3/4. Transaksi rutin dan nilainya bagus.",
        "action": "🛡️ **Pertahankan.** Tawarkan program loyalty atau bundling untuk meningkatkan nilai transaksi.",
        "color": "#66bd63" # Hijau
    },
    "Potential Loyalist": {
        "desc": "Baru menjadi pelanggan dengan nilai transaksi rata-rata, potensi jadi loyal.",
        "action": "📈 **Upsell.** Ajak mereka agar lebih sering bertransaksi. Tawarkan insentif untuk order berikutnya.",
        "color": "#a6d96a" # Hijau Muda
    },
    "New Customers": {
        "desc": "Baru pertama kali bertransaksi (Recency tinggi, Frequency rendah).",
        "action": "👋 **Onboarding.** Pastikan pengalaman pertama mereka mulus agar mereka kembali lagi.",
        "color": "#d9ef8b" # Kuning Kehijauan
    },
    "Promising": {
        "desc": "Pelanggan baru dengan nilai transaksi yang menjanjikan.",
        "action": "🤝 **Engagement.** Bangun hubungan personal agar mereka menjadi Loyal.",
        "color": "#ffffbf" # Kuning Pucat
    },
    "Need Attention": {
        "desc": "Recency, Frequency, Monetary di level menengah-bawah.",
        "action": "⚠️ **Re-aktivasi.** Sapa mereka, tawarkan promo terbatas untuk memancing transaksi.",
        "color": "#fee08b" # Kuning
    },
    "About to Sleep": {
        "desc": "Recency dan Frequency mulai menurun. Berisiko hilang.",
        "action": "⏰ **Wake Up Call.** Hubungi sebelum mereka benar-benar lupa. Tanyakan kendala.",
        "color": "#fdae61" # Oranye
    },
    "At Risk": {
        "desc": "Dulu sering beli/nilai besar, tapi SUDAH LAMA tidak kembali.",
        "action": "🚨 **URGENT.** Ini adalah 'Mantan Juara'. Lakukan kunjungan/call personal segera untuk memenangkan kembali.",
        "color": "#f46d43" # Oranye Kemerahan
    },
    "Can't Lose Them": {
        "desc": "Pelanggan 'Paus' (Nilai Besar) yang sudah sangat lama tidak aktif.",
        "action": "🔥 **Win-Back.** Cari tahu kenapa mereka pergi (Pindah kompetitor?). Tawarkan insentif khusus.",
        "color": "#d73027" # Merah
    },
    "Hibernating": {
        "desc": "Jarang beli dan sudah lama sekali tidak aktif.",
        "action": "💤 **Low Priority.** Coba email marketing otomatis. Jangan habiskan resource sales berlebih.",
        "color": "#a50026" # Merah Tua
    },
    "Lost": {
        "desc": "Skor terendah di semua aspek (R=1, F=1, M=1).",
        "action": "❌ **Abaikan.** Fokuskan energi ke segmen lain yang lebih potensial.",
        "color": "#000000" # Hitam
    },
    "Others": {
        "desc": "Tidak masuk kategori spesifik di atas.",
        "action": "Analisa lebih lanjut jika jumlahnya besar.",
        "color": "#808080" # Abu-abu
    }
}

# Urutan Tampilan di Grafik (Dari Terbaik ke Terburuk)
SEGMENT_ORDER = list(SEGMENT_INFO.keys())

# ==========================================
# 🔐 1. SISTEM LOGIN
# ==========================================
def check_password():
    def password_entered():
        if st.session_state["password"] == "episi2025":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    st.title("🔒 KSO SCISI Dashboard Login")
    st.text_input("Password:", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Password salah.")
    return False

if not check_password():
    st.stop()

# ==========================================
# 🚀 2. APLIKASI UTAMA
# ==========================================

@st.cache_data
def load_data():
    # Load RFM
    rfm_df = pd.read_csv('data_rfm_processed.csv')
    # Pastikan kolom Segment bertipe kategori sesuai urutan kita agar sorting benar
    rfm_df['Segment'] = pd.Categorical(rfm_df['Segment'], categories=SEGMENT_ORDER, ordered=True)
    
    # Load Transaksi
    part1 = pd.read_csv('transaksi_part1.csv')
    part2 = pd.read_csv('transaksi_part2.csv')
    trx_df = pd.concat([part1, part2], ignore_index=True)
    trx_df['ls_date'] = pd.to_datetime(trx_df['ls_date'])
    trx_df['YearMonth'] = trx_df['ls_date'].dt.to_period('M').astype(str)
    
    return rfm_df, trx_df

try:
    rfm, transactions = load_data()
except FileNotFoundError:
    st.error("Data CSV tidak ditemukan.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.title("Navigasi")
st.sidebar.success("Login Berhasil ✅")
page = st.sidebar.radio("Pilih Halaman:", ["Overview & RFM", "Cari Importir", "Kamus Segmen"])

st.sidebar.divider()
st.sidebar.info(f"Total Importir: {rfm['importer_name'].nunique():,}")

# --- PAGE 1: OVERVIEW & RFM ---
if page == "Overview & RFM":
    st.title("📊 Dashboard Segmentasi Pelanggan (RFM)")
    
    # 1. BAR CHART SEGMENTASI (UTAMA)
    st.subheader("Distribusi Pelanggan per Segmen")
    
    # Agregasi Data
    seg_counts = rfm['Segment'].value_counts().reset_index()
    seg_counts.columns = ['Segment', 'Count']
    # Urutkan berdasarkan urutan custom kita (Champions -> Lost)
    seg_counts['Segment'] = pd.Categorical(seg_counts['Segment'], categories=SEGMENT_ORDER, ordered=True)
    seg_counts = seg_counts.sort_values('Segment')
    
    # Buat Color Map untuk Plotly
    color_map = {seg: info['color'] for seg, info in SEGMENT_INFO.items()}
    
    fig = px.bar(
        seg_counts, 
        x='Segment', 
        y='Count', 
        color='Segment',
        color_discrete_map=color_map,
        text='Count', # Tampilkan angka di atas bar
        title="Jumlah Pelanggan per Kategori (Urutan Prioritas)"
    )
    fig.update_layout(height=500, xaxis_title=None, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # 2. PENJELASAN & TOP 5 (Expanders)
    st.subheader("📋 Detail Segmen & Top Customer")
    st.markdown("Klik panah di bawah untuk melihat strategi dan daftar pelanggan teratas.")
    
    # Loop untuk membuat Expander setiap segmen
    for segment in SEGMENT_ORDER:
        # Hanya tampilkan jika ada datanya
        count = len(rfm[rfm['Segment'] == segment])
        if count > 0:
            info = SEGMENT_INFO.get(segment, SEGMENT_INFO['Others'])
            
            # Buat Expander dengan Warna Indikator (Emoji)
            with st.expander(f"**{segment}** ({count} Pelanggan)"):
                # Kolom 1: Penjelasan & Strategi
                c1, c2 = st.columns([2, 3])
                with c1:
                    st.info(f"**Kriteria:** {info['desc']}")
                    st.warning(f"**Fokus Strategi:** {info['action']}")
                
                # Kolom 2: Tabel Top 5
                with c2:
                    st.write("**🏆 Top 5 Pelanggan (Nilai Tertinggi):**")
                    top_5 = rfm[rfm['Segment'] == segment].sort_values(by='Monetary', ascending=False).head(5)
                    
                    disp_df = top_5[['importer_name', 'Monetary', 'Recency_days']].copy()
                    disp_df.columns = ['Nama Importir', 'Total Nilai (USD)', 'Hari Terakhir']
                    disp_df['Total Nilai (USD)'] = disp_df['Total Nilai (USD)'].apply(lambda x: f"${x:,.0f}")
                    
                    st.dataframe(disp_df, hide_index=True, use_container_width=True)

# --- PAGE 2: CARI IMPORTIR ---
elif page == "Cari Importir":
    st.title("🔍 Cari & Analisa Importir")
    
    search_term = st.text_input("Ketik Nama Importir (Min. 3 huruf):", placeholder="Contoh: 3M Indo...")
    selected_importer = None
    
    if len(search_term) >= 3:
        matches = rfm[rfm['importer_name'].str.contains(search_term, case=False, na=False)]
        if matches.empty:
            st.warning("Tidak ditemukan.")
        else:
            importer_list = matches['importer_name'].tolist()
            st.success(f"Ditemukan {len(importer_list)} hasil.")
            selected_importer = st.selectbox("Pilih Importir:", importer_list, index=None, placeholder="Klik untuk memilih...")
    
    if selected_importer:
        st.divider()
        st.header(f"🏢 {selected_importer}")
        
        # Data RFM
        cust_rfm = rfm[rfm['importer_name'] == selected_importer].iloc[0]
        seg_info = SEGMENT_INFO.get(cust_rfm['Segment'], {})
        
        # Tampilkan status dengan warna
        st.markdown(f"### Status: <span style='color:{seg_info.get('color', 'black')}'>{cust_rfm['Segment']}</span>", unsafe_allow_html=True)
        st.info(f"**Rekomendasi:** {seg_info.get('action', '-')}")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Transaksi", f"{cust_rfm['Frequency']:,}")
        c2.metric("Total Nilai (USD)", f"${cust_rfm['Monetary']:,.2f}")
        c3.metric("Terakhir Transaksi", f"{cust_rfm['Recency_days']} hari lalu")
        
        # Data Transaksi
        cust_trx = transactions[transactions['importer_name'] == selected_importer].copy()
        
        if not cust_trx.empty:
            monthly_trend = cust_trx.groupby('YearMonth')['NILAI (USD)'].sum().reset_index()
            fig = px.bar(monthly_trend, x='YearMonth', y='NILAI (USD)', title="Trend Transaksi Bulanan")
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("Riwayat Transaksi")
            st.dataframe(cust_trx[['ls_date', 'Commodity', 'NILAI (USD)', 'Status Kompetisi']].sort_values('ls_date', ascending=False), use_container_width=True)

# --- PAGE 3: KAMUS SEGMEN ---
elif page == "Kamus Segmen":
    st.title("📖 Kamus Segmen RFM")
    st.markdown("Panduan definisi dan strategi untuk setiap segmen pelanggan.")
    
    for seg in SEGMENT_ORDER:
        info = SEGMENT_INFO[seg]
        with st.container():
            st.markdown(f"### <span style='color:{info['color']}'>█</span> {seg}", unsafe_allow_html=True)
            st.markdown(f"**Siapa mereka?** {info['desc']}")
            st.markdown(f"**Apa yang harus dilakukan?** {info['action']}")
            st.divider()