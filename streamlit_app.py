import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Kasa Pro v14.0", layout="wide")

TR_AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
ALT_KATEGORILER = ["Market", "Yakıt", "Sağlık", "Giyim", "Hobi", "Evişleri", "Dışarıda Yemek", "Diğer"]

# --- VERİ YÖNETİMİ ---
if 'manual_data' not in st.session_state:
    st.session_state.manual_data = pd.DataFrame(columns=['id', 'Tarih', 'Kategori', 'Açıklama', 'Gelir', 'Gider', 'Kart', 'Tur'])
if 'edit_id' not in st.session_state:
    st.session_state.edit_id = None

# --- OTOMATİK HESAPLAMA (SALİ/CUMA VE SABİT GÜNLER) ---
def get_monthly_recurring(year, month):
    items = []
    num_days = calendar.monthrange(year, month)[1]
    # Salı/Cuma ve Sabit Günler (Kodun önceki versiyonundaki kurallar aynen geçerli)
    for d in range(1, num_days + 1):
        curr = date(year, month, d)
        if curr.weekday() == 1: items.append({'id': f'auto_pazar_{curr}', 'Tarih': curr, 'Kategori': 'Pazar Gideri', 'Açıklama': 'Haftalık', 'Gider': 1500.0, 'Gelir': 0, 'Kart': 0, 'Tur': 'Gider'})
        if curr.weekday() == 4: items.append({'id': f'auto_hafta_{curr}', 'Tarih': curr, 'Kategori': 'Haftalık', 'Açıklama': 'Haftalık Gelir', 'Gider': 0, 'Gelir': 1900.0, 'Kart': 0, 'Tur': 'Gelir'})
    
    rules = [ (1, 'Yemek', 'Yemek 1', 3200, 'Gelir'), (2, 'Maaş', 'Maaş', 37555.07, 'Gelir'), (2, 'Elden', 'Elden', 30640, 'Gelir'), (5, 'Garanti KK', 'Ödeme', 37000, 'Gider'), (15, 'İgdaş', 'Fatura', 2500, 'Gider')]
    for d, k, a, t, tur in rules:
        if d <= num_days: items.append({'id': f'auto_{k}_{month}', 'Tarih': date(year, month, d), 'Kategori': k, 'Açıklama': a, 'Gelir': t if tur == 'Gelir' else 0, 'Gider': t if tur == 'Gider' else 0, 'Kart': 0, 'Tur': tur})
    return pd.DataFrame(items)

# --- ANA EKRAN VE YAN PANEL ---
with st.sidebar:
    st.header("➕ Yeni İşlem")
    with st.form("yeni_islem"):
        f_tarih = st.date_input("Tarih", date.today())
        f_tur = st.selectbox("Tür", ["Gelir", "Gider", "Kredi Kartı"])
        f_kat = st.selectbox("Kategori", ALT_KATEGORILER)
        f_acik = st.text_input("Açıklama")
        f_tut = st.number_input("Tutar", min_value=0.0)
        if st.form_submit_button("Kaydet"):
            new_row = {'id': str(datetime.now().timestamp()), 'Tarih': f_tarih, 'Kategori': f_kat, 'Açıklama': f_acik, 'Gelir': f_tut if f_tur == 'Gelir' else 0, 'Gider': f_tut if f_tur == 'Gider' else 0, 'Kart': f_tut if f_tur == 'Kredi Kartı' else 0, 'Tur': f_tur}
            st.session_state.manual_data = pd.concat([st.session_state.manual_data, pd.DataFrame([new_row])], ignore_index=True)
            st.rerun()

st.title("🏦 Kasa Pro v14.0")
secili_ay_ad = st.selectbox("Ay Seçin", TR_AYLAR, index=date.today().month - 1)
ay_idx = TR_AYLAR.index(secili_ay_ad) + 1

# Veri Birleştirme ve Devir Hesaplama (Basitleştirilmiş)
auto_df = get_monthly_recurring(2026, ay_idx)
man_df = st.session_state.manual_data.copy()
if not man_df.empty: 
    man_df['Tarih'] = pd.to_datetime(man_df['Tarih']).dt.date
    man_df = man_df[pd.to_datetime(man_df['Tarih']).dt.month == ay_idx]
full_df = pd.concat([auto_df, man_df], ignore_index=True).sort_values('Tarih')

# --- TABLO VE GÜNCELLEME/SİL BUTONLARI ---
st.subheader(f"📊 {secili_ay_ad} Ayı Hareketleri")

# Başlıklar
h1, h2, h3, h4, h5 = st.columns([1, 2, 1, 1, 1.5])
h1.write("**Tarih**")
h2.write("**Kategori/Açıklama**")
h3.write("**Tutar**")
h4.write("**Tür**")
h5.write("**İşlemler**")

for idx, row in full_df.iterrows():
    c1, c2, c3, c4, c5 = st.columns([1, 2, 1, 1, 1.5])
    tutar = max(row['Gelir'], row['Gider'], row['Kart'])
    
    # DÜZENLEME MODU AÇIK MI?
    if st.session_state.edit_id == row['id']:
        with c2: edit_acik = st.text_input("Açıklama", row['Açıklama'], key=f"ac_{idx}")
        with c3: edit_tut = st.number_input("Tutar", value=float(tutar), key=f"tu_{idx}")
        with c5:
            if st.button("Kaydet ✅", key=f"sv_{idx}"):
                if "auto" in str(row['id']):
                    st.error("Sistem ödemesi düzenlenemez.")
                else:
                    m_idx = st.session_state.manual_data[st.session_state.manual_data['id'] == row['id']].index[0]
                    st.session_state.manual_data.at[m_idx, 'Açıklama'] = edit_acik
                    st.session_state.manual_data.at[m_idx, row['Tur']] = edit_tut
                    st.session_state.edit_id = None
                    st.rerun()
            if st.button("İptal ❌", key=f"can_{idx}"):
                st.session_state.edit_id = None
                st.rerun()
    else:
        # NORMAL GÖRÜNÜM
        c1.write(row['Tarih'].strftime('%d-%m'))
        c2.write(f"**{row['Kategori']}** - {row['Açıklama']}")
        c3.write(f"{tutar:,.2f} TL")
        c4.write(row['Tur'])
        with c5:
            col_edit, col_del = st.columns(2)
            if col_edit.button("Güncelle ✏️", key=f"ed_{idx}"):
                st.session_state.edit_id = row['id']
                st.rerun()
            if col_del.button("Sil 🗑️", key=f"dl_{idx}"):
                if "auto" in str(row['id']):
                    st.error("Sabit ödeme silinemez.")
                else:
                    st.session_state.manual_data = st.session_state.manual_data[st.session_state.manual_data['id'] != row['id']]
                    st.rerun()

# --- ÖZET METRİKLER (EN ALTA ALINDI) ---
st.divider()
st.metric("Net Kalan (Bu Ay)", f"{(full_df['Gelir'].sum() - full_df['Gider'].sum() - full_df['Kart'].sum()):,.2f} TL")
