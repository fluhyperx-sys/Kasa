import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="Kasa Pro v11.1", layout="wide")

# --- VERİ SAKLAMA ---
if 'data' not in st.session_state:
    # 1 Mart 2026 itibariyle tanımlanan düzenli veriler
    initial_data = [
        # GELİRLER
        {'Tarih': date(2026, 3, 2), 'Kategori': 'Maaş', 'Açıklama': 'Düzenli Maaş', 'Gelir': 37555.07, 'Gider': 0, 'Kart': 0, 'Tur': 'Gelir'},
        {'Tarih': date(2026, 3, 2), 'Kategori': 'Elden', 'Açıklama': 'Düzenli Elden', 'Gelir': 30640.00, 'Gider': 0, 'Kart': 0, 'Tur': 'Gelir'},
        {'Tarih': date(2026, 3, 1), 'Kategori': 'Yemek', 'Açıklama': 'Yemek Kartı 1', 'Gelir': 3200.00, 'Gider': 0, 'Kart': 0, 'Tur': 'Gelir'},
        {'Tarih': date(2026, 3, 15), 'Kategori': 'Yemek', 'Açıklama': 'Yemek Kartı 2', 'Gelir': 3000.00, 'Gider': 0, 'Kart': 0, 'Tur': 'Gelir'},
        # GİDERLER
        {'Tarih': date(2026, 3, 5), 'Kategori': 'Sheri BES', 'Açıklama': 'Düzenli Ödeme', 'Gelir': 0, 'Gider': 2000.00, 'Kart': 0, 'Tur': 'Gider'},
        {'Tarih': date(2026, 3, 5), 'Kategori': 'Batu TEL', 'Açıklama': 'Düzenli Ödeme', 'Gelir': 0, 'Gider': 810.75, 'Kart': 0, 'Tur': 'Gider'},
        {'Tarih': date(2026, 3, 5), 'Kategori': 'Garanti KK', 'Açıklama': 'Düzenli Ödeme', 'Gelir': 0, 'Gider': 37000.00, 'Kart': 0, 'Tur': 'Gider'},
        {'Tarih': date(2026, 3, 15), 'Kategori': 'İski SU', 'Açıklama': 'Fatura', 'Gelir': 0, 'Gider': 750.00, 'Kart': 0, 'Tur': 'Gider'},
        {'Tarih': date(2026, 3, 15), 'Kategori': 'Sheri TEL', 'Açıklama': 'Fatura', 'Gelir': 0, 'Gider': 431.00, 'Kart': 0, 'Tur': 'Gider'},
        {'Tarih': date(2026, 3, 15), 'Kategori': 'İgdaş Doğal Gaz', 'Açıklama': 'Fatura', 'Gelir': 0, 'Gider': 2500.00, 'Kart': 0, 'Tur': 'Gider'},
        {'Tarih': date(2026, 3, 19), 'Kategori': 'Enpara Kr', 'Açıklama': 'Kredi Taksidi', 'Gelir': 0, 'Gider': 23627.83, 'Kart': 0, 'Tur': 'Gider'}
    ]
    st.session_state.data = pd.DataFrame(initial_data)

# --- ANA BAŞLIK ---
st.title("🏦 Kasa Finans Yönetimi v11.1")

# --- SOL PANEL: VERİ GİRİŞİ ---
with st.sidebar:
    st.header("➕ Yeni İşlem")
    with st.form("ekleme_formu", clear_on_submit=True):
        f_tarih = st.date_input("İşlem Tarihi", date.today())
        f_tur = st.selectbox("İşlem Türü", ["Gelir", "Gider", "Kredi Kartı"])
        f_kat = st.selectbox("Kategori", ["Maaş", "Elden", "Yemek", "Haftalık", "Pazar Gideri", "Fatura", "Kredi", "Diğer"])
        f_acik = st.text_input("İşlem Açıklaması")
        f_tut = st.number_input("Tutar (TL)", min_value=0.0, step=10.0)
        submit = st.form_submit_button("Sisteme Kaydet")

    if submit:
        if f_tut > 0:
            # Mükerrer Kontrolü
            is_dup = not st.session_state.data[
                (st.session_state.data['Tarih'] == f_tarih) & 
                (st.session_state.data['Kategori'] == f_kat) & 
                ((st.session_state.data['Gelir'] == f_tut) | (st.session_state.data['Gider'] == f_tut) | (st.session_state.data['Kart'] == f_tut))
            ].empty
            
            if is_dup:
                st.error("⚠️ Bu kayıt zaten mevcut! (Mükerrer Giriş)")
            else:
                yeni = {
                    'Tarih': f_tarih, 'Kategori': f_kat, 'Açıklama': f_acik,
                    'Gelir': f_tut if f_tur == 'Gelir' else 0,
                    'Gider': f_tut if f_tur == 'Gider' else 0,
                    'Kart': f_tut if f_tur == 'Kredi Kartı' else 0,
                    'Tur': f_tur
                }
                st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([yeni])], ignore_index=True)
                st.success("✅ Kayıt Başarılı")
                st.rerun()

# --- ANALİZ VE TABLOLAR ---
aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
secili_ay_ad = st.selectbox("Görüntülenen Ay:", aylar, index=date.today().month - 1)
ay_no = aylar.index(secili_ay_ad) + 1

# Veri Hazırlama
df = st.session_state.data.copy()
df['Tarih'] = pd.to_datetime(df['Tarih'])

# ÖZEL KURAL: Enpara Kr Eylül 19, 2026'dan sonra görünmez
df = df[~((df['Kategori'] == 'Enpara Kr') & (df['Tarih'] > pd.Timestamp(2026, 9, 20)))]

# Seçili Ayı Filtrele
aylik_df = df[df['Tarih'].dt.month == ay_no].sort_values(by='Tarih')

# --- ÖZET METRİKLER ---
c1, c2, c3, c4 = st.columns(4)
top_gelir = aylik_df['Gelir'].sum()
top_gider = aylik_df['Gider'].sum()
top_kart = aylik_df['Kart'].sum()
kalan = top_gelir - (top_gider + top_kart)

c1.metric("Toplam Gelir", f"{top_gelir:,.2f} TL")
c2.metric("Nakit Gider", f"{top_gider:,.2f} TL")
c3.metric("Kart Borcu", f"{top_kart:,.2f} TL")
c4.metric("Net Kalan", f"{kalan:,.2f} TL")

# --- TABLAR ---
t1, t2, t3, t4 = st.tabs(["📋 Tüm İşlemler", "💰 Gelirler", "💸 Giderler", "💳 Kart Harcamaları"])

with t1:
    st.subheader(f"{secili_ay_ad} Ayı Tüm Hareketler")
    if not aylik_df.empty:
        for i, row in aylik_df.iterrows():
            col1, col2, col3, col4 = st.columns([1, 2, 1, 0.5])
            col1.write(row['Tarih'].strftime('%d-%m-%Y'))
            col2.write(f"**{row['Kategori']}** - {row['Açıklama']}")
            tutar_goster = max(row['Gelir'], row['Gider'], row['Kart'])
            col3.write(f"{tutar_goster:,.2f} TL")
            if col4.button("🗑️", key=f"btn_{i}"):
                st.session_state.data = st.session_state.data.drop(i)
                st.rerun()
    else:
        st.info("Bu aya ait veri bulunmuyor.")

with t2:
    st.subheader("Gelir Listesi")
    st.dataframe(aylik_df[aylik_df['Tur'] == 'Gelir'][['Tarih', 'Kategori', 'Açıklama', 'Gelir']], use_container_width=True)

with t3:
    st.subheader("Nakit Gider Listesi")
    st.dataframe(aylik_df[aylik_df['Tur'] == 'Gider'][['Tarih', 'Kategori', 'Açıklama', 'Gider']], use_container_width=True)

with t4:
    st.subheader("Kredi Kartı Harcamaları")
    st.dataframe(aylik_df[aylik_df['Tur'] == 'Kredi Kartı'][['Tarih', 'Kategori', 'Açıklama', 'Kart']], use_container_width=True)
