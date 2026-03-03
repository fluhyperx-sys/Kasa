import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Kasa Pro v15.0", layout="wide")

# --- TÜRKÇE AYARLARI VE KATEGORİLER ---
TR_AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
ALT_KATEGORILER = ["Market", "Yakıt", "Sağlık", "Giyim", "Hobi", "Evişleri", "Dışarıda Yemek", "Diğer"]

# --- VERİ YÖNETİMİ ---
if 'manual_data' not in st.session_state:
    st.session_state.manual_data = pd.DataFrame(columns=['id', 'Tarih', 'Kategori', 'Açıklama', 'Gelir', 'Gider', 'Kart', 'Tur'])
if 'edit_id' not in st.session_state:
    st.session_state.edit_id = None

# --- OTOMATİK HESAPLAMA SİSTEMİ ---
def get_monthly_recurring(year, month):
    items = []
    num_days = calendar.monthrange(year, month)[1]
    
    # Salı ve Cuma Günleri
    for d in range(1, num_days + 1):
        curr = date(year, month, d)
        if curr.weekday() == 1: # Salı
            items.append({'id': f'auto_p_{curr}', 'Tarih': curr, 'Kategori': 'Pazar Gideri', 'Açıklama': 'Düzenli', 'Gider': 1500.0, 'Gelir': 0, 'Kart': 0, 'Tur': 'Gider'})
        if curr.weekday() == 4: # Cuma
            items.append({'id': f'auto_h_{curr}', 'Tarih': curr, 'Kategori': 'Haftalık', 'Açıklama': 'Düzenli', 'Gider': 0, 'Gelir': 1900.0, 'Kart': 0, 'Tur': 'Gelir'})
    
    # Sabit Günler
    rules = [
        (1, 'Yemek', 'Yemek 1', 3200, 'Gelir'), (2, 'Maaş', 'Ana Maaş', 37555.07, 'Gelir'),
        (2, 'Elden', 'Ek Gelir', 30640, 'Gelir'), (5, 'Sheri BES', 'Düzenli', 2000, 'Gider'),
        (5, 'Batu TEL', 'Düzenli', 810.75, 'Gider'), (5, 'Garanti KK', 'Ödeme', 37000, 'Gider'),
        (15, 'İski SU', 'Fatura', 750, 'Gider'), (15, 'Sheri TEL', 'Fatura', 431, 'Gider'),
        (15, 'İgdaş Doğal Gaz', 'Fatura', 2500, 'Gider'), (15, 'Yemek', 'Yemek Kartı 2', 3000, 'Gelir'),
    ]
    for d, k, a, t, tur in rules:
        if d <= num_days:
            items.append({'id': f'auto_{k}_{month}_{d}', 'Tarih': date(year, month, d), 'Kategori': k, 'Açıklama': a, 'Gelir': t if tur == 'Gelir' else 0, 'Gider': t if tur == 'Gider' else 0, 'Kart': 0, 'Tur': tur})

    # Enpara Kr
    if date(year, month, 1) <= date(2026, 9, 19):
        items.append({'id': f'auto_enp_{month}', 'Tarih': date(year, month, 19), 'Kategori': 'Enpara Kr', 'Açıklama': 'Kredi', 'Gider': 23627.83, 'Gelir': 0, 'Kart': 0, 'Tur': 'Gider'})
    
    return pd.DataFrame(items)

# --- YAN PANEL: YENİ GİRİŞ ---
with st.sidebar:
    st.header("➕ Manuel İşlem")
    with st.form("sidebar_form", clear_on_submit=True):
        f_tarih = st.date_input("Tarih", date.today())
        f_tur = st.selectbox("Tür", ["Gelir", "Gider", "Kredi Kartı"])
        f_kat = st.selectbox("Kategori", ALT_KATEGORILER + ["Diğer Gelir"])
        f_acik = st.text_input("Açıklama")
        f_tut = st.number_input("Tutar", min_value=0.0)
        if st.form_submit_button("Kaydet"):
            new_id = str(datetime.now().timestamp())
            new_row = {'id': new_id, 'Tarih': f_tarih, 'Kategori': f_kat, 'Açıklama': f_acik, 'Gelir': f_tut if f_tur == 'Gelir' else 0, 'Gider': f_tut if f_tur == 'Gider' else 0, 'Kart': f_tut if f_tur == 'Kredi Kartı' else 0, 'Tur': f_tur}
            st.session_state.manual_data = pd.concat([st.session_state.manual_data, pd.DataFrame([new_row])], ignore_index=True)
            st.rerun()

# --- ANA EKRAN ---
st.title("🏦 Kasa Pro v15.0")
secili_ay_ad = st.selectbox("İnceleme Ayı", TR_AYLAR, index=date.today().month - 1)
ay_idx = TR_AYLAR.index(secili_ay_ad) + 1

# Veri Birleştirme ve Devir Hesabı
auto_df = get_monthly_recurring(2026, ay_idx)
man_df = st.session_state.manual_data.copy()
if not man_df.empty:
    man_df['Tarih'] = pd.to_datetime(man_df['Tarih']).dt.date
    man_df = man_df[pd.to_datetime(man_df['Tarih']).dt.month == ay_idx]
full_df = pd.concat([auto_df, man_df], ignore_index=True).sort_values('Tarih')

# Özet Metrikler
c1, c2, c3, c4 = st.columns(4)
ay_gelir, ay_gider, ay_kart = full_df['Gelir'].sum(), full_df['Gider'].sum(), full_df['Kart'].sum()
c1.metric("Bu Ay Gelir", f"{ay_gelir:,.2f} TL")
c2.metric("Nakit Gider", f"{ay_gider:,.2f} TL")
c3.metric("Kart Harcaması", f"{ay_kart:,.2f} TL")
c4.metric("Ay Sonu Kalan", f"{(ay_gelir - ay_gider - ay_kart):,.2f} TL")

# --- SEKME YAPISI (v13 Benzeri) ---
tab1, tab2, tab3 = st.tabs(["💰 Gelirler", "💸 Nakit Giderler", "💳 Kredi Kartı"])

def tablo_olustur(df_subset, tur_etiketi):
    if df_subset.empty:
        st.info(f"Bu ay için {tur_etiketi} kaydı bulunmuyor.")
        return

    # Başlıklar
    h1, h2, h3, h4 = st.columns([1, 2, 1, 1.5])
    h1.write("**Tarih**")
    h2.write("**Açıklama**")
    h3.write("**Tutar**")
    h4.write("**İşlemler**")

    for idx, row in df_subset.iterrows():
        c1, c2, c3, c4 = st.columns([1, 2, 1, 1.5])
        tutar = max(row['Gelir'], row['Gider'], row['Kart'])
        
        if st.session_state.edit_id == row['id']:
            with c2: edit_acik = st.text_input("Düzenle", row['Açıklama'], key=f"edit_ac_{row['id']}")
            with c3: edit_tut = st.number_input("Tutar", value=float(tutar), key=f"edit_tu_{row['id']}")
            with c4:
                if st.button("Kaydet ✅", key=f"save_{row['id']}"):
                    if "auto" in str(row['id']):
                        st.warning("Sabit ödemeler otomatik hesaplanır. Manuel girişi düzenleyebilirsiniz.")
                    else:
                        m_idx = st.session_state.manual_data[st.session_state.manual_data['id'] == row['id']].index[0]
                        st.session_state.manual_data.at[m_idx, 'Açıklama'] = edit_acik
                        st.session_state.manual_data.at[m_idx, row['Tur']] = edit_tut
                        st.session_state.edit_id = None
                        st.rerun()
                if st.button("İptal ❌", key=f"cancel_{row['id']}"):
                    st.session_state.edit_id = None
                    st.rerun()
        else:
            c1.write(row['Tarih'].strftime('%d-%m'))
            c2.write(f"**{row['Kategori']}** - {row['Açıklama']}")
            c3.write(f"{tutar:,.2f} TL")
            with c4:
                col_e, col_d = st.columns(2)
                if col_e.button("✏️", key=f"ed_{row['id']}"):
                    st.session_state.edit_id = row['id']
                    st.rerun()
                if col_d.button("🗑️", key=f"dl_{row['id']}"):
                    if "auto" in str(row['id']):
                        st.error("Sabit ödeme silinemez.")
                    else:
                        st.session_state.manual_data = st.session_state.manual_data[st.session_state.manual_data['id'] != row['id']]
                        st.rerun()

with tab1: tablo
