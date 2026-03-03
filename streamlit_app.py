import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar

# --- AYARLAR ---
st.set_page_config(page_title="Kasa Pro v12.0", layout="wide")

# --- FONKSİYONLAR: TEKRARLAYAN ÖDEME HESAPLAMA ---
def get_monthly_recurring(year, month):
    items = []
    num_days = calendar.monthrange(year, month)[1]
    
    # 1. Her Ayın Salı Günleri (Pazar Gideri - 1500 TL)
    for d in range(1, num_days + 1):
        if date(year, month, d).weekday() == 1: # 1 = Salı
            items.append({'Tarih': date(year, month, d), 'Kategori': 'Pazar Gideri', 'Açıklama': 'Haftalık Pazar', 'Gider': 1500.0, 'Gelir': 0, 'Kart': 0, 'Tur': 'Gider'})
            
    # 2. Her Ayın Cuma Günleri (Haftalık Gelir - 1900 TL)
    for d in range(1, num_days + 1):
        if date(year, month, d).weekday() == 4: # 4 = Cuma
            items.append({'Tarih': date(year, month, d), 'Kategori': 'Haftalık', 'Açıklama': 'Haftalık Gelir', 'Gider': 0, 'Gelir': 1900.0, 'Kart': 0, 'Tur': 'Gelir'})

    # 3. Ayın Belirli Günleri
    static_rules = [
        (1, 'Yemek', 'Yemek Kartı 1', 3200, 'Gelir'),
        (2, 'Maaş', 'Ana Maaş', 37555.07, 'Gelir'),
        (2, 'Elden', 'Ek Gelir', 30640, 'Gelir'),
        (5, 'Sheri BES', 'Düzenli', 2000, 'Gider'),
        (5, 'Batu TEL', 'Düzenli', 810.75, 'Gider'),
        (5, 'Garanti KK', 'Kredi Kartı Ödemesi', 37000, 'Gider'),
        (15, 'İski SU', 'Fatura', 750, 'Gider'),
        (15, 'Sheri TEL', 'Fatura', 431, 'Gider'),
        (15, 'İgdaş Doğal Gaz', 'Fatura', 2500, 'Gider'),
        (15, 'Yemek', 'Yemek Kartı 2', 3000, 'Gelir'),
    ]
    
    for day, cat, desc, amt, tur in static_rules:
        if day <= num_days:
            items.append({
                'Tarih': date(year, month, day), 'Kategori': cat, 'Açıklama': desc,
                'Gelir': amt if tur == 'Gelir' else 0,
                'Gider': amt if tur == 'Gider' else 0,
                'Kart': 0, 'Tur': tur
            })

    # 4. Enpara Kr (Eylül 2026'ya kadar)
    if date(year, month, 1) <= date(2026, 9, 19):
        items.append({'Tarih': date(year, month, 19), 'Kategori': 'Enpara Kr', 'Açıklama': 'Kredi Taksidi', 'Gider': 23627.83, 'Gelir': 0, 'Kart': 0, 'Tur': 'Gider'})
        
    return pd.DataFrame(items)

# --- VERİ YÖNETİMİ ---
if 'manual_data' not in st.session_state:
    st.session_state.manual_data = pd.DataFrame(columns=['Tarih', 'Kategori', 'Açıklama', 'Gelir', 'Gider', 'Kart', 'Tur'])

# --- ARAYÜZ ---
st.title("📊 Kasa Pro v12.0 - Akıllı Bütçe")

with st.sidebar:
    st.header("➕ Manuel İşlem")
    with st.form("entry_form", clear_on_submit=True):
        f_tarih = st.date_input("Tarih", date.today())
        f_tur = st.selectbox("Tür", ["Gelir", "Gider", "Kredi Kartı"])
        f_kat = st.text_input("Kategori (Market, Yakıt vb.)")
        f_acik = st.text_input("Açıklama")
        f_tut = st.number_input("Tutar", min_value=0.0)
        if st.form_submit_button("Kaydet"):
            new_row = {'Tarih': f_tarih, 'Kategori': f_kat, 'Açıklama': f_acik, 'Gelir': f_tut if f_tur == 'Gelir' else 0, 'Gider': f_tut if f_tur == 'Gider' else 0, 'Kart': f_tut if f_tur == 'Kredi Kartı' else 0, 'Tur': f_tur}
            st.session_state.manual_data = pd.concat([st.session_state.manual_data, pd.DataFrame([new_row])], ignore_index=True)
            st.rerun()

# --- AY SEÇİMİ VE VERİ BİRLEŞTİRME ---
aylar = list(calendar.month_name)[1:]
secili_ay_ad = st.selectbox("İnceleme Ayı", aylar, index=date.today().month - 1)
ay_index = aylar.index(secili_ay_ad) + 1
yil = 2026 # Sabitlendi

# Otomatik ve Manuel Verileri Birleştir
auto_df = get_monthly_recurring(yil, ay_index)
man_df = st.session_state.manual_data.copy()
if not man_df.empty:
    man_df['Tarih'] = pd.to_datetime(man_df['Tarih']).dt.date
    man_df = man_df[pd.to_datetime(man_df['Tarih']).dt.month == ay_index]

full_df = pd.concat([auto_df, man_df], ignore_index=True).sort_values('Tarih')

# --- ÖZET ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Gelir", f"{full_df['Gelir'].sum():,.2f} TL")
c2.metric("Nakit Gider", f"{full_df['Gider'].sum():,.2f} TL")
c3.metric("Kart", f"{full_df['Kart'].sum():,.2f} TL")
c4.metric("Kalan", f"{(full_df['Gelir'].sum() - full_df['Gider'].sum() - full_df['Kart'].sum()):,.2f} TL")

# --- TABLAR VE DÜZENLEME ---
t1, t2, t3, t4 = st.tabs(["📋 Tüm Hareketler", "💰 Gelir", "💸 Gider", "💳 Kart"])

with t1:
    for i, row in full_df.iterrows():
        with st.expander(f"{row['Tarih']} | {row['Kategori']} | {max(row['Gelir'], row['Gider'], row['Kart']):,.2f} TL"):
            # DÜZENLEME FORMU
            with st.form(key=f"edit_form_{i}"):
                new_desc = st.text_input("Açıklama", row['Açıklama'])
                new_amt = st.number_input("Tutar", value=float(max(row['Gelir'], row['Gider'], row['Kart'])))
                col_btn1, col_btn2 = st.columns(2)
                if col_btn1.form_submit_button("Güncelle 💾"):
                    # Veriyi güncelleme mantığı
                    if i < len(auto_df): # Otomatik veri ise manuel listeye kopyala ve oradan yönet
                         st.warning("Düzenli ödemeler otomatik hesaplanır. Kalıcı değişiklik için kodu güncelleyebiliriz.")
                    else:
                        idx = i - len(auto_df)
                        st.session_state.manual_data.at[idx, 'Açıklama'] = new_desc
                        if row['Tur'] == 'Gelir': st.session_state.manual_data.at[idx, 'Gelir'] = new_amt
                        elif row['Tur'] == 'Gider': st.session_state.manual_data.at[idx, 'Gider'] = new_amt
                        else: st.session_state.manual_data.at[idx, 'Kart'] = new_amt
                        st.success("Güncellendi!")
                        st.rerun()
                
                if col_btn2.form_submit_button("Sil 🗑️"):
                    if i >= len(auto_df):
                        st.session_state.manual_data = st.session_state.manual_data.drop(i - len(auto_df)).reset_index(drop=True)
                        st.rerun()
                    else:
                        st.error("Sistem ödemeleri silinemez, sadece manuel eklenenler silinebilir.")

with t2: st.dataframe(full_df[full_df['Tur'] == 'Gelir'], use_container_width=True)
with t3: st.dataframe(full_df[full_df['Tur'] == 'Gider'], use_container_width=True)
with t4: st.dataframe(full_df[full_df['Tur'] == 'Kredi Kartı'], use_container_width=True)
