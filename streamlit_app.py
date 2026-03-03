import streamlit as st
import pandas as pd
from datetime import datetime

# Sayfa Yapılandırması
st.set_page_config(page_title="Kasa Bütçe v1.0", layout="wide")

# Veri Saklama (Session State)
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=['Tarih', 'Kategori', 'Açıklama', 'Gelir', 'Gider', 'Kart'])

# Sabit Gelir/Gider Tanımları
SABIT_GELIRLER = ["Maaş", "Yan Haklar", "Ek Gelir"]
SABIT_GIDERLER = ["Kira/Kredi", "Faturalar", "Mutfak", "Ulaşım", "Eğitim", "Diğer"]

st.title("📊 Kasa - Kişisel Finans Yönetimi")

# --- VERİ GİRİŞ ALANI ---
with st.expander("Yeni İşlem Ekle", expanded=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        tarih = st.date_input("İşlem Tarihi", datetime.now())
        tur = st.selectbox("İşlem Türü", ["Gelir", "Gider", "Kredi Kartı"])
    with col2:
        kategoriler = SABIT_GELIRLER if tur == "Gelir" else SABIT_GIDERLER
        kategori = st.selectbox("Kategori", kategoriler)
        aciklama = st.text_input("Açıklama")
    with col3:
        tutar = st.number_input("Tutar (TL)", min_value=0.0, step=100.0)
        ekle_btn = st.button("İşlemi Kaydet")

    if ekle_btn and tutar > 0:
        yeni_veri = {
            'Tarih': pd.to_datetime(tarih),
            'Kategori': kategori,
            'Açıklama': aciklama,
            'Gelir': tutar if tur == "Gelir" else 0,
            'Gider': tutar if tur == "Gider" else 0,
            'Kart': tutar if tur == "Kredi Kartı" else 0
        }
        st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([yeni_veri])], ignore_index=True)
        st.success("Kaydedildi!")

# --- ANALİZ ---
st.divider()
aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
secili_ay_ad = st.selectbox("Analiz Ayı", aylar, index=datetime.now().month - 1)
ay_no = aylar.index(secili_ay_ad) + 1

df = st.session_state.data.copy()
if not df.empty:
    df['Tarih'] = pd.to_datetime(df['Tarih'])
    df['Ay'] = df['Tarih'].dt.month
    
    # Mevcut Ay Verileri
    mevcut_ay_df = df[df['Ay'] == ay_no]
    
    # Özet Metrikleri
    c1, c2, c3 = st.columns(3)
    gelir_toplam = mevcut_ay_df['Gelir'].sum()
    gider_toplam = mevcut_ay_df['Gider'].sum() + mevcut_ay_df['Kart'].sum()
    
    c1.metric("Bu Ay Toplam Gelir", f"{gelir_toplam:,.2f} TL")
    c2.metric("Bu Ay Toplam Gider", f"{gider_toplam:,.2f} TL")
    c3.metric("Net Durum", f"{(gelir_toplam - gider_toplam):,.2f} TL")

    # GRAFİK BÖLÜMÜ (Hata Veren Kısım Düzenlendi)
    if not mevcut_ay_df.empty:
        st.write("### Harcama Dağılımı")
        
        # Sadece Gider ve Kart olan satırları al
        harcamalar = mevcut_ay_df[(mevcut_ay_df['Gider'] > 0) | (mevcut_ay_df['Kart'] > 0)]
        
        if not harcamalar.empty:
            # Kategoriye göre grupla ve toplam harcamayı (Nakit+Kart) hesapla
            grafik_verisi = harcamalar.groupby('Kategori')[['Gider', 'Kart']].sum().sum(axis=1)
            
            # Eğer veri hala boş değilse grafiği çiz
            if not grafik_verisi.empty:
                st.plotly_chart = st.bar_chart(grafik_verisi) # pie_chart yerine daha stabil olan bar_chart deniyoruz
            else:
                st.info("Gösterilecek grafik verisi bulunamadı.")
        else:
            st.info("Bu ay için harcama kaydı yok.")

        st.write("### İşlem Detayları")
        st.dataframe(mevcut_ay_df, use_container_width=True)
else:
    st.warning("Henüz hiç veri girmediniz. Lütfen yukarıdan işlem ekleyin.")
