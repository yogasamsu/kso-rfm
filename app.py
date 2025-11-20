import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURATION ---
st.set_page_config(
    page_title="KSO SCISI - Customer Dashboard",
    page_icon="📊",
    layout="wide"
)

# ==========================================
# 🔐 1. SISTEM PASSWORD SEDERHANA
# ==========================================
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == "episi2025":  # <--- GANTI PASSWORD DISINI
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Hapus password dari memori
        else:
            st.session_state["password_correct"] = False

    # Inisialisasi session state
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    # Jika sudah login, return True
    if st.session_state["password_correct"]:
        return True

    # Tampilan Login Form
    st.title("🔒 KSO SCISI Dashboard Login")
    st.text_input(
        "Masukkan Password:", 
        type="password", 
        on_change=password_entered, 
        key="password"
    )
    
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Password salah. Silakan coba lagi.")

    return False

# CEK PASSWORD SEBELUM MEMUAT KONTEN LAIN
if not check_password():
    st.stop()  # Berhenti di sini jika belum login

# ==========================================
# 🚀 2. APLIKASI UTAMA (Hanya jalan jika login sukses)
# ==========================================

# --- LOAD DATA FUNCTION (Cached) ---
@st.cache_data
def load_data():
    # Load RFM Summary
    rfm_df = pd.read_csv('data_rfm_processed.csv')
    
    # Load Transaction Data (Combine parts)
    part1 = pd.read_csv('transaksi_part1.csv')
    part2 = pd.read_csv('transaksi_part2.csv')
    trx_df = pd.concat([part1, part2], ignore_index=True)
    
    # Convert Date
    trx_df['ls_date'] = pd.to_datetime(trx_df['ls_date'])
    trx_df['YearMonth'] = trx_df['ls_date'].dt.to_period('M').astype(str)
    
    return rfm_df, trx_df

# Load Data
try:
    rfm, transactions = load_data()
except FileNotFoundError:
    st.error("Data tidak ditemukan. Pastikan file csv ada di folder yang sama.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.title("Navigasi")
st.sidebar.success("Login Berhasil ✅") # Indikator login
page = st.sidebar.radio("Pilih Halaman:", ["Overview & RFM", "Cari Importir"])

st.sidebar.divider()
st.sidebar.info(f"Total Importir: {rfm['importer_name'].nunique():,}")
st.sidebar.info(f"Total Transaksi: {len(transactions):,}")

# --- PAGE 1: OVERVIEW & RFM ---
if page == "Overview & RFM":
    st.title("📊 Dashboard Customer KSO SCISI")
    st.markdown("Analisa segmentasi pelanggan menggunakan metode RFM (Recency, Frequency, Monetary).")
    
    # 1. TREEMAP RFM
    st.subheader("Peta Segmentasi Pelanggan (RFM)")
    
    # Siapkan data untuk Treemap
    treemap_data = rfm.groupby('Segment').agg(
        Count=('importer_name', 'count'),
        Total_Value=('Monetary', 'sum')
    ).reset_index()
    
    # Buat Label Persentase
    total_cust = treemap_data['Count'].sum()
    treemap_data['Label'] = treemap_data.apply(
        lambda x: f"{x['Segment']}<br>({(x['Count']/total_cust)*100:.1f}%)", axis=1
    )
    
    # Plotly Treemap
    fig = px.treemap(
        treemap_data, 
        path=['Label'], 
        values='Count',
        color='Segment',
        color_discrete_map={
            'Champions': '#006400', 'Loyal Customers': '#32CD32',
            'Potential Loyalist': '#90EE90', 'New Customers': '#FFFF00',
            'At Risk': '#FFA500', "Can't Lose Them": '#FF4500',
            'Hibernating': '#8B0000', 'Lost': '#000000', 'Others': '#D3D3D3'
        },
        title="Proporsi Jumlah Pelanggan per Segmen"
    )
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    # 2. TOP 5 PER CLUSTER
    st.subheader("🏆 Top 5 Customer per Cluster")
    st.markdown("Importir dengan nilai transaksi (Monetary) tertinggi di setiap segmen.")
    
    segments = rfm['Segment'].unique()
    
    cols = st.columns(3)
    for i, segment in enumerate(segments):
        with cols[i % 3]:
            st.markdown(f"**{segment}**")
            top_5 = rfm[rfm['Segment'] == segment].sort_values(by='Monetary', ascending=False).head(5)
            display_df = top_5[['importer_name', 'Monetary']].copy()
            display_df['Monetary'] = display_df['Monetary'].apply(lambda x: f"${x:,.0f}")
            st.dataframe(display_df, hide_index=True, use_container_width=True)

# --- PAGE 2: CARI IMPORTIR & DETAIL ---
elif page == "Cari Importir":
    st.title("🔍 Pencarian & Detail Importir")
    
    # 1. SEARCH BAR
    search_term = st.text_input("Ketik Nama Importir (Minimal 3 huruf):", placeholder="Contoh: 3M Indo...")
    
    selected_importer = None
    
    if len(search_term) >= 3:
        # Filter data
        matches = rfm[rfm['importer_name'].str.contains(search_term, case=False, na=False)]
        
        if matches.empty:
            st.warning("Tidak ditemukan importir dengan nama tersebut.")
        else:
            # Dropdown list
            importer_list = matches['importer_name'].tolist()
            
            st.write(f"Ditemukan {len(importer_list)} hasil pencarian:")
            
            # --- PERBAIKAN DROPDOWN ---
            selected_importer = st.selectbox(
                "⬇️ Klik di sini untuk memilih Importir dari hasil pencarian:", 
                importer_list, 
                index=None, # Default kosong
                placeholder="Pilih salah satu importir..."
            )
    
    # 2. DETAIL VIEW
    if selected_importer:
        st.divider()
        st.header(f"🏢 {selected_importer}")
        
        # Ambil data RFM Importir ini
        cust_rfm = rfm[rfm['importer_name'] == selected_importer].iloc[0]
        
        # Tampilkan Metrics Cluster (Row 1)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Segmen RFM", cust_rfm['Segment'])
        col2.metric("Total Transaksi (Freq)", f"{cust_rfm['Frequency']:,}")
        col3.metric("Total Nilai (Monetary)", f"${cust_rfm['Monetary']:,.2f}")
        col4.metric("Hari Terakhir (Recency)", f"{cust_rfm['Recency_days']} hari lalu")
        
        # Filter Data Transaksi untuk Importir ini
        cust_trx = transactions[transactions['importer_name'] == selected_importer].copy()
        
        # Tabulasi Detail
        tab1, tab2, tab3 = st.tabs(["📈 Trend Transaksi", "📦 Komoditas", "📋 Data Mentah"])
        
        with tab1:
            st.subheader("Trend Nilai Transaksi Bulanan")
            if not cust_trx.empty:
                monthly_trend = cust_trx.groupby('YearMonth')['NILAI (USD)'].sum().reset_index()
                
                fig_trend = px.bar(
                    monthly_trend, 
                    x='YearMonth', 
                    y='NILAI (USD)',
                    title=f"Riwayat Transaksi: {selected_importer}",
                    labels={'YearMonth': 'Bulan', 'NILAI (USD)': 'Nilai (USD)'},
                    color_discrete_sequence=['#1f77b4']
                )
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.write("Data transaksi tidak tersedia.")
        
        with tab2:
            st.subheader("Komposisi Komoditas")
            if 'Commodity' in cust_trx.columns:
                comm_dist = cust_trx.groupby('Commodity')['NILAI (USD)'].sum().reset_index()
                fig_pie = px.pie(
                    comm_dist, 
                    values='NILAI (USD)', 
                    names='Commodity',
                    title='Distribusi Nilai per Komoditas',
                    hole=0.4
                )
                st.plotly_chart(fig_pie, use_container_width=True)
                
                st.dataframe(comm_dist.sort_values('NILAI (USD)', ascending=False), hide_index=True, use_container_width=True)
            else:
                st.write("Kolom 'Commodity' tidak ditemukan di data transaksi.")

        with tab3:
            st.subheader("History Transaksi Lengkap")
            cols_to_show = ['ls_number', 'ls_date', 'Commodity', 'NILAI (USD)', 'Status Kompetisi']
            valid_cols = [c for c in cols_to_show if c in cust_trx.columns]
            
            st.dataframe(
                cust_trx[valid_cols].sort_values(by='ls_date', ascending=False), 
                use_container_width=True,
                hide_index=True
            )