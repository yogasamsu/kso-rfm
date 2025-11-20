import pandas as pd
import numpy as np
import os

# --- KONFIGURASI ---
INPUT_FILE = 'transaksi_kso.csv'
OUTPUT_RFM = 'data_rfm_processed.csv'
OUTPUT_PART1 = 'transaksi_part1.csv'
OUTPUT_PART2 = 'transaksi_part2.csv'

print("--- Memulai Pre-processing Data ---")

# 1. Memuat Data
if os.path.exists(INPUT_FILE):
    print(f"Membaca {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE)
    
    # Konversi tipe data dasar
    if 'ls_date' in df.columns:
        df['ls_date'] = pd.to_datetime(df['ls_date'], errors='coerce')
    if 'NILAI (USD)' in df.columns and df['NILAI (USD)'].dtype == object:
        df['NILAI (USD)'] = pd.to_numeric(df['NILAI (USD)'].astype(str).str.replace(',', ''), errors='coerce')
    
    # 2. Menghitung RFM (Sama seperti logika sebelumnya)
    print("Menghitung RFM & Segmentasi...")
    snapshot_date = df['ls_date'].max() + pd.Timedelta(days=1)
    
    rfm = df.groupby('importer_name').agg(
        Recency_days=('ls_date', lambda x: (snapshot_date - x.max()).days),
        Frequency=('ls_number', 'count') if 'ls_number' in df.columns else ('ls_date', 'count'),
        Monetary=('NILAI (USD)', 'sum')
    ).reset_index()
    
    # Skor RFM
    rfm['R_Score'] = pd.qcut(rfm['Recency_days'], 4, labels=[4, 3, 2, 1], duplicates='drop')
    rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 4, labels=[1, 2, 3, 4], duplicates='drop')
    rfm['M_Score'] = pd.qcut(rfm['Monetary'].rank(method='first'), 4, labels=[1, 2, 3, 4], duplicates='drop')
    
    # Fungsi Segmentasi Detail
    def rfm_segment_detail(row):
        r, f, m = str(row['R_Score']), str(row['F_Score']), str(row['M_Score'])
        if r == 'nan' or f == 'nan' or m == 'nan': return 'Others'
        rf = r + f
        if rf in ['44', '43', '34', '33']:
            if m == '4': return 'Champions'
            if m == '3': return 'Loyal Customers'
            if m == '2': return 'Potential Loyalist'
            if m == '1': return 'Promising'
        if rf in ['42', '41', '32', '31']:
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

    rfm['Segment'] = rfm.apply(rfm_segment_detail, axis=1)
    
    # Simpan Data RFM (Ringkas)
    rfm.to_csv(OUTPUT_RFM, index=False)
    print(f"File RFM tersimpan: {OUTPUT_RFM}")

    # 3. Memecah Data Transaksi (Split)
    print("Memecah file transaksi...")
    half_point = len(df) // 2
    part1 = df.iloc[:half_point]
    part2 = df.iloc[half_point:]
    
    part1.to_csv(OUTPUT_PART1, index=False)
    part2.to_csv(OUTPUT_PART2, index=False)
    print(f"File Split tersimpan: {OUTPUT_PART1} & {OUTPUT_PART2}")
    
    print("--- Selesai! Sekarang Anda siap membuat Dashboard. ---")

else:
    print(f"Error: File {INPUT_FILE} tidak ditemukan.")