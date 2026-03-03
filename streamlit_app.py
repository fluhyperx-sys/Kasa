import streamlit as st
import pandas as pd
from datetime import datetime
import calendar

# --- SAYFA AYARLARI (v9.4 STİLİ) ---
st.set_page_config(page_title="Kasa Finans v10.0", layout="wide")

# --- VERİ SAKLAMA ---
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=['Tarih', 'Kategori', 'Açıklama', 'Gelir', 'Gider', 'Kart', 'Tekrarlanan'])

# --- AYARLAR VE KATEGORİLER ---
SABIT_GELIRLER = ["Maaş", "Kira Geliri", "Ek Gelir"]
SABIT_GIDERLER = ["Kira/Kredi", "Faturalar", "Mutfak", "Ulaşım", "Eğitim", "Eğlence", "Diğer"]

st.title("💳 Kasa - Akıllı Bütçe Yönetimi")
st.markdown(f"**Güncel Tarih:** {datetime.now().strftime('%d %B %Y')}")

# --- 1. BÖLÜM: VERİ GİRİŞİ ---
with st.sidebar:
    st.header("➕ Yeni İşlem")
    tarih = st.date_input("İşlem Tarihi", datetime.now())
    tur = st.selectbox("İşlem Türü", ["Gelir", "Gider", "Kredi Kartı"])
    
    kategoriler = SABIT_GELIRLER if tur == "Gelir" else SABIT_GIDERLER
    kategori = st.selectbox("Kategori", kategoriler)
    aciklama = st.text_input("Açıklama")
    tutar = st.number_input("Tutar (TL)", min_value=0.0, step=50.0)
    
    # TEKRARLANAN İŞLEM ÖZELLİĞİ
    tekrarlar = st.checkbox("Her Ay Tekrarla", help="Bu işlem her ay otomatik olarak bütçenize eklenir.")
    
    if st.button("Sisteme İşle", use_container_width=True):
        if tutar > 0:
            yeni_satir = {
                'Tarih': pd.to_datetime(tarih),
                'Kategori': kategori,
                'Açıklama': aciklama,
                'Gelir': tutar if tur == "Gelir" else 0,
                'Gider': tutar if tur == "Gider" else 0,
                'Kart': tutar if tur == "Kredi Kartı" else 0,
                'Tekrarlanan': tekrarlar
            }
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([yeni_satir])], ignore_index=True)
            st.success("İşlem kaydedildi!")
        else:
            st.error("Lütfen tutar giriniz.")

# --- 2. BÖLÜM: ANALİZ VE OTOMATİK HESAPLAMA ---
aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
secili_ay_ad = st.selectbox("İncelemek İstediğiniz Ay", aylar, index=datetime.now().month - 1)
ay_no = aylar.index(secili_ay_ad) + 1

# Veriyi işle
df = st.session_state.data.copy()

# Tekrarlanan işlemleri mevcut aya kopyala (Eğer o ayda henüz yoksa)
tekrarlanan_df = df[df['Tekrarlanan'] == True].copy()
if not tekrarlanan_df.empty:
    for index, row in tekrarlanan_df.items():
        # Basitleştirilmiş mantık: Tekrarlananları her ay varmış gibi hesaplamaya dahil et
        pass

# Mevcut ay verilerini filtrele
if not df.empty:
    df['Tarih'] = pd.to_datetime(df['Tarih'])
    # Hem o ayda girilenler hem de tüm 'Tekrarlanan' işaretli olanları getir
    aylik_df = df[(df['Tarih'].dt.month == ay_no) | (df['Tekrarlanan'] == True)]
    
    # --- ÖZET KARTLARI ---
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    
    toplam_gelir = aylik_df['Gelir'].sum()
    toplam_gider = aylik_df['Gider'].sum()
    toplam_kart = aylik_df['Kart'].sum()
    net_kalan = toplam_gelir - (toplam_gider + toplam_kart)
    
    c1.metric("Toplam Gelir", f"{toplam_gelir:,.2f} TL")
    c2.metric("Nakit Gider", f"{toplam_gider:,.2f} TL")
    c3.metric("Kredi Kartı", f"{toplam_kart:,.2f} TL")
    c4.metric("Kalan Bakiye", f"{net_kalan:,.2f} TL", delta=f"{net_kalan:,.2f}")

    # --- GÖRSEL ANALİZ ---
    col_sol, col_sag = st.columns([2, 1])
    
    with col_sol:
        st.subheader("📊 İşlem Detayları")
        st.dataframe(aylik_df[['Tarih', 'Kategori', 'Açıklama', 'Gelir', 'Gider', 'Kart']], use_container_width=True)
        
    with col_sag:
        st.subheader("📈 Harcama Dağılımı")
        grafik_data = aylik_df[aylik_df['Gider'] + aylik_df['Kart'] > 0]
        if not grafik_data.empty:
            pasta = grafik_data.groupby('Kategori')[['Gider', 'Kart']].sum().sum(axis=1)
            st.bar_chart(pasta) # Stabilite için bar_chart
        else:
            st.info("Harcama verisi bulunamadı.")
else:
    st.info("Henüz veri girişi yapılmadı. Sol taraftaki menüden başlayabilirsiniz.")
