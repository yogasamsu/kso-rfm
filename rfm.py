import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os # Untuk cek lokasi file

print("--- Analisa RFM dari File Lokal (VS Code / Mac) ---")

# --- 1. MEMUAT DATA LOKAL ---
# Pastikan file ini ada di folder yang sama dengan script Anda
filename = 'transaksi_kso.csv'

if os.path.exists(filename):
    print(f"Membaca file: {filename}...")
    try:
        df = pd.read_csv(filename)
        print(f"Data berhasil dimuat! Total baris: {len(df)}")
        
        # --- 2. PEMBERSIHAN DATA ---
        # Konversi Tanggal
        if 'ls_date' in df.columns:
            df['ls_date'] = pd.to_datetime(df['ls_date'], errors='coerce')
        
        # Konversi Numerik (Bersihkan koma jika ada)
        if 'NILAI (USD)' in df.columns:
            if df['NILAI (USD)'].dtype == object:
                df['NILAI (USD)'] = df['NILAI (USD)'].astype(str).str.replace(',', '')
            df['NILAI (USD)'] = pd.to_numeric(df['NILAI (USD)'], errors='coerce')

        # Hapus data kosong di kolom penting
        df.dropna(subset=['ls_date', 'NILAI (USD)', 'importer_name'], inplace=True)
        
        # --- 3. HITUNG RFM (ALL COMMODITIES) ---
        print("Menghitung RFM...")
        # Tentukan tanggal snapshot (1 hari setelah transaksi terakhir di data)
        snapshot_date = df['ls_date'].max() + pd.Timedelta(days=1)
        
        # Ekstrak Bulan/Tahun Data untuk nama file output
        analisis_bulan = snapshot_date.strftime('%Y-%m')

        rfm_data_all = df.groupby('importer_name').agg(
            Recency_days=('ls_date', lambda x: (snapshot_date - x.max()).days),
            Frequency=('ls_number', 'count') if 'ls_number' in df.columns else ('ls_date', 'count'),
            Monetary=('NILAI (USD)', 'sum')
        ).reset_index()

        # --- 4. HITUNG SKOR & SEGMEN ---
        # Menggunakan qcut untuk membagi menjadi 4 kuartil (1-4)
        rfm_data_all['R_Score'] = pd.qcut(rfm_data_all['Recency_days'], 4, labels=[4, 3, 2, 1], duplicates='drop')
        rfm_data_all['F_Score'] = pd.qcut(rfm_data_all['Frequency'].rank(method='first'), 4, labels=[1, 2, 3, 4], duplicates='drop')
        rfm_data_all['M_Score'] = pd.qcut(rfm_data_all['Monetary'].rank(method='first'), 4, labels=[1, 2, 3, 4], duplicates='drop')

        # Fungsi Segmentasi Detail
        def rfm_segment_detail(row):
            # Handle potential NaN values
            if pd.isna(row['R_Score']) or pd.isna(row['F_Score']) or pd.isna(row['M_Score']):
                return 'Others'

            r = str(row['R_Score'])
            f = str(row['F_Score'])
            m = str(row['M_Score'])
            
            rf_score = r + f

            # Logika Segmentasi
            if rf_score in ['44', '43', '34', '33']:
                if m == '4': return 'Champions'
                if m == '3': return 'Loyal Customers'
                if m == '2': return 'Potential Loyalist'
                if m == '1': return 'Promising'
                
            if rf_score in ['42', '41', '32', '31']:
                if m in ['4', '3']: return 'New Customers' 
                if m in ['2', '1']: return 'Need Attention' 
                
            if r == '2':
                if f in ['4', '3']: return 'At Risk'
                if f == '2': return 'About to Sleep'
                if f == '1': return 'Hibernating'
                
            if r == '1':
                if f in ['4', '3']: return "Can't Lose Them"
                if f == '2': return 'Hibernating'
                if f == '1': return 'Lost'
                
            return 'Others'

        rfm_data_all['Segment'] = rfm_data_all.apply(rfm_segment_detail, axis=1)
        
        # Tambahkan info waktu analisa ke dalam file
        rfm_data_all['Tanggal_Snapshot'] = snapshot_date

        # --- 5. PREVIEW HASIL ---
        print("\nRingkasan Segmen:")
        print(rfm_data_all['Segment'].value_counts())
        
        print("\nContoh 5 Data Teratas:")
        print(rfm_data_all.head())

        # --- 6. SIMPAN KE CSV (LOKAL) ---
        output_filename = f'Hasil_Analisa_RFM_{analisis_bulan}.csv'
        
        # Simpan file di folder yang sama dengan script
        rfm_data_all.to_csv(output_filename, index=False)
        
        print("\n" + "="*50)
        print(f"SUKSES! File hasil analisa telah disimpan sebagai:")
        print(f"👉 {output_filename}")
        print("Cek folder tempat Anda menyimpan script python ini.")
        print("="*50)

    except Exception as e:
        print(f"Terjadi kesalahan saat memproses data: {e}")
else:
    print(f"ERROR: File '{filename}' tidak ditemukan di folder ini.")
    print(f"Lokasi script saat ini: {os.getcwd()}")
    print("Pastikan file csv ada di lokasi tersebut.")