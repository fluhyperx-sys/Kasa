import streamlit as st
import pandas as pd
from datetime import datetime

# Sayfa Yapılandırması
st.set_page_config(page_title="Bütçe Takip Sistemi v9.10", layout="wide")

# Veri Saklama (Session State)
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=['Tarih', 'Kategori', 'Açıklama', 'Gelir', 'Gider', 'Kart'])

# Sabit Gelir/Gider Tanımları
SABIT_GELIRLER = ["Maaş", "Yan Haklar", "Ek Gelir"]
SABIT_GIDERLER = ["Kira/Kredi", "Faturalar", "Mutfak", "Ulaşım", "Eğitim", "Diğer"]

st.title("📊 Kişisel Bütçe ve Finans Yönetimi")

# --- VERİ GİRİŞ ALANI ---
with st.expander("Yeni İşlem Ekle", expanded=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        tarih = st.date_value = st.date_input("İşlem Tarihi", datetime.now())
        tur = st.selectbox("İşlem Türü", ["Gelir", "Gider", "Kredi Kartı"])
    with col2:
        kategoriler = SABIT_GELIRLER if tur == "Gelir" else SABIT_GIDERLER
        kategori = st.selectbox("Kategori", kategoriler)
        aciklama = st.text_input("Açıklama (Örn: Market, İnternet vb.)")
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
        st.success("İşlem başarıyla eklendi!")

# --- ANALİZ VE DEVİR HESAPLAMA ---
st.divider()
secili_ay = st.sidebar.month_input = st.selectbox("Analiz Edilecek Ay", 
                                                ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
                                                 "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"],
                                                index=datetime.now().month - 1)

ay_index = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
            "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"].index(secili_ay) + 1

# Verileri Filtrele
df = st.session_state.data.copy()
df['Tarih'] = pd.to_datetime(df['Tarih'])
df['Ay'] = df['Tarih'].dt.month

# Geçmişten Gelen Devir Hesaplama (Seçili aydan önceki tüm aylar)
gecmis_df = df[df['Ay'] < ay_index]
toplam_gelir_gecmis = gecmis_df['Gelir'].sum()
toplam_gider_gecmis = gecmis_df['Gider'].sum()
toplam_kart_gecmis = gecmis_df['Kart'].sum()
devir_bakiyesi = toplam_gelir_gecmis - (toplam_gider_gecmis + toplam_kart_gecmis)

# Mevcut Ay Verileri
mevcut_ay_df = df[df['Ay'] == ay_index]
mevcut_gelir = mevcut_ay_df['Gelir'].sum()
mevcut_gider = mevcut_ay_df['Gider'].sum()
mevcut_kart = mevcut_ay_df['Kart'].sum()

# Özet Tablosu
st.subheader(f"📅 {secili_ay} Ayı Özeti")
c1, c2, c3, c4 = st.columns(4)

with c1:
    color = "normal" if devir_bakiyesi >= 0 else "inverse"
    st.metric("Geçmişten Devir", f"{devir_bakiyesi:,.2f} TL", delta_color=color)
with c2:
    st.metric("Bu Ay Gelir", f"{mevcut_gelir:,.2f} TL")
with c3:
    st.metric("Bu Ay Gider (Nakit + Kart)", f"{(mevcut_gider + mevcut_kart):,.2f} TL")
with c4:
    net_durum = devir_bakiyesi + mevcut_gelir - (mevcut_gider + mevcut_kart)
    st.metric("Ay Sonu Kalan", f"{net_durum:,.2f} TL")

# Grafik ve Detaylar
if not mevcut_ay_df.empty:
    st.write("### Harcama Dağılımı")
    gider_ozet = mevcut_ay_df[mevcut_ay_df['Gider'] > 0].groupby('Kategori')['Gider'].sum()
    if not gider_ozet.empty:
        st.pie_chart(gider_ozet)
    # Grafik ve Detaylar (Hata vermemesi için güncellendi)
if not mevcut_ay_df.empty:
    st.write("### Harcama Dağılımı")
    
    # Sadece Gider ve Kredi Kartı olanları filtrele
    harcama_df = mevcut_ay_df[(mevcut_ay_df['Gider'] > 0) | (mevcut_ay_df['Kart'] > 0)]
    
    if not harcama_df.empty:
        # Gider ve Kart toplamını kategori bazlı birleştir
        gider_ozet = harcama_df.groupby('Kategori')[['Gider', 'Kart']].sum().sum(axis=1)
        st.pie_chart(gider_ozet)
    else:
        st.info("Bu ay için henüz bir harcama (Gider veya Kart) kaydı bulunmuyor.")
    
    st.write("### İşlem Kayıtları")
    st.dataframe(mevcut_ay_df, use_container_width=True)
    st.write("### İşlem Kayıtları")
    st.dataframe(mevcut_ay_df, use_container_width=True)
else:
    st.info(f"{secili_ay} ayına ait henüz bir veri girişi yapılmamış.")
