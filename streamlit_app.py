import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar

# --- AYARLAR ---
st.set_page_config(page_title="Kasa Pro v13.0", layout="wide")

# --- TÜRKÇE AYARLARI ---
TR_AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
ALT_KATEGORILER = ["Market", "Yakıt", "Sağlık", "Giyim", "Hobi", "Evişleri", "Dışarıda Yemek", "Diğer"]

# --- FONKSİYONLAR: OTOMATİK HESAPLAMA ---
def get_monthly_recurring(year, month):
    items = []
    num_days = calendar.monthrange(year, month)[1]
    
    # Her Ayın Salı Günleri (Pazar Gideri)
    for d in range(1, num_days + 1):
        if date(year, month, d).weekday() == 1: # 1 = Salı
            items.append({'Tarih': date(year, month, d), 'Kategori': 'Pazar Gideri', 'Açıklama': 'Haftalık Pazar', 'Gider': 1500.0, 'Gelir': 0, 'Kart': 0, 'Tur': 'Gider'})
            
    # Her Ayın Cuma Günleri (Haftalık Gelir)
    for d in range(1, num_days + 1):
        if date(year, month, d).weekday() == 4: # 4 = Cuma
            items.append({'Tarih': date(year, month, d), 'Kategori': 'Haftalık', 'Açıklama': 'Haftalık Gelir', 'Gider': 0, 'Gelir': 1900.0, 'Kart': 0, 'Tur': 'Gelir'})

    # Ayın Belirli Günleri
    rules = [
        (1, 'Yemek', 'Yemek Kartı 1', 3200, 'Gelir'), (2, 'Maaş', 'Ana Maaş', 37555.07, 'Gelir'),
        (2, 'Elden', 'Ek Gelir', 30640, 'Gelir'), (5, 'Sheri BES', 'Düzenli', 2000, 'Gider'),
        (5, 'Batu TEL', 'Düzenli', 810.75, 'Gider'), (5, 'Garanti KK', 'Kredi Kartı Ödemesi', 37000, 'Gider'),
        (15, 'İski SU', 'Fatura', 750, 'Gider'), (15, 'Sheri TEL', 'Fatura', 431, 'Gider'),
        (15, 'İgdaş Doğal Gaz', 'Fatura', 2500, 'Gider'), (15, 'Yemek', 'Yemek Kartı 2', 3000, 'Gelir'),
    ]
    for day, cat, desc, amt, tur in rules:
        if day <= num_days:
            items.append({'Tarih': date(year, month, day), 'Kategori': cat, 'Açıklama': desc, 'Gelir': amt if tur == 'Gelir' else 0, 'Gider': amt if tur == 'Gider' else 0, 'Kart': 0, 'Tur': tur})

    # Enpara Kr Kontrolü
    if date(year, month, 1) <= date(2026, 9, 19):
        items.append({'Tarih': date(year, month, 19), 'Kategori': 'Enpara Kr', 'Açıklama': 'Kredi Taksidi', 'Gider': 23627.83, 'Gelir': 0, 'Kart': 0, 'Tur': 'Gider'})
        
    return pd.DataFrame(items)

# --- VERİ YÖNETİMİ ---
if 'manual_data' not in st.session_state:
    st.session_state.manual_data = pd.DataFrame(columns=['Tarih', 'Kategori', 'Açıklama', 'Gelir', 'Gider', 'Kart', 'Tur'])

# --- YAN PANEL ---
with st.sidebar:
    st.header("➕ Manuel İşlem")
    with st.form("entry_form", clear_on_submit=True):
        f_tarih = st.date_input("Tarih", date.today())
        f_tur = st.selectbox("Tür", ["Gelir", "Gider", "Kredi Kartı"])
        f_kat = st.selectbox("Kategori", ALT_KATEGORILER)
        f_acik = st.text_input("Açıklama")
        f_tut = st.number_input("Tutar", min_value=0.0)
        if st.form_submit_button("Kaydet"):
            new_row = {'Tarih': f_tarih, 'Kategori': f_kat, 'Açıklama': f_acik, 'Gelir': f_tut if f_tur == 'Gelir' else 0, 'Gider': f_tur == 'Gider' and f_tut or 0, 'Kart': f_tur == 'Kredi Kartı' and f_tut or 0, 'Tur': f_tur}
            st.session_state.manual_data = pd.concat([st.session_state.manual_data, pd.DataFrame([new_row])], ignore_index=True)
            st.rerun()

# --- ANA EKRAN ---
st.title("🏦 Kasa Pro v13.0 - Akıllı Bütçe")
secili_ay_ad = st.selectbox("İnceleme Ayı", TR_AYLAR, index=date.today().month - 1)
ay_index = TR_AYLAR.index(secili_ay_ad) + 1

# --- BAKİYE DEVİR HESABI ---
gecmis_gelir, gecmis_gider, gecmis_kart = 0, 0, 0
for m in range(3, ay_index): # Mart'tan (3) başlar
    m_df = pd.concat([get_monthly_recurring(2026, m), st.session_state.manual_data[pd.to_datetime(st.session_state.manual_data['Tarih']).dt.month == m]], ignore_index=True)
    gecmis_gelir += m_df['Gelir'].sum()
    gecmis_gider += m_df['Gider'].sum()
    gecmis_kart += m_df['Kart'].sum()
devir_bakiyesi = gecmis_gelir - (gecmis_gider + gecmis_kart)

# Mevcut Ay Verileri
auto_df = get_monthly_recurring(2026, ay_index)
man_df = st.session_state.manual_data.copy()
if not man_df.empty:
    man_df['Tarih'] = pd.to_datetime(man_df['Tarih']).dt.date
    man_df = man_df[pd.to_datetime(man_df['Tarih']).dt.month == ay_index]

full_df = pd.concat([auto_df, man_df], ignore_index=True).sort_values('Tarih')

# --- ÖZET KARTLARI ---
c1, c2, c3, c4 = st.columns(4)
ay_gelir = full_df['Gelir'].sum()
ay_gider = full_df['Gider'].sum()
ay_kart = full_df['Kart'].sum()

c1.metric("Geçmişten Devir", f"{devir_bakiyesi:,.2f} TL")
c2.metric("Bu Ay Gelir", f"{ay_gelir:,.2f} TL")
c3.metric("Bu Ay Gider (Nakit+Kart)", f"{(ay_gider + ay_kart):,.2f} TL")
c4.metric("Net Kalan (Toplam)", f"{(devir_bakiyesi + ay_gelir - ay_gider - ay_kart):,.2f} TL")

# --- TABLAR ---
t1, t2, t3, t4 = st.tabs(["📋 Tüm Hareketler", "💰 Gelir", "💸 Gider", "💳 Kart"])
with t1:
    for i, row in full_df.iterrows():
        with st.expander(f"{row['Tarih'].strftime('%d %B')} | {row['Kategori']} | {max(row['Gelir'], row['Gider'], row['Kart']):,.2f} TL"):
            st.write(f"**Açıklama:** {row['Açıklama']}")
            if i >= len(auto_df) and st.button("Sil 🗑️", key=f"del_{i}"):
                st.session_state.manual_data = st.session_state.manual_data.drop(i - len(auto_df)).reset_index(drop=True)
                st.rerun()

with t2: st.dataframe(full_df[full_df['Tur'] == 'Gelir'], use_container_width=True)
with t3: st.dataframe(full_df[full_df['Tur'] == 'Gider'], use_container_width=True)
with t4: st.dataframe(full_df[full_df['Tur'] == 'Kredi Kartı'], use_container_width=True)
    
