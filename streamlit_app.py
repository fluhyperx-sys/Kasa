import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="Kasa Pro v16.0", layout="wide")

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
            items.append({'id': f'auto_p_{month}_{d}', 'Tarih': curr, 'Kategori': 'Pazar Gideri', 'Açıklama': 'Düzenli', 'Gider': 1500.0, 'Gelir': 0, 'Kart': 0, 'Tur': 'Gider'})
        if curr.weekday() == 4: # Cuma
            items.append({'id': f'auto_h_{month}_{d}', 'Tarih': curr, 'Kategori': 'Haftalık', 'Açıklama': 'Düzenli', 'Gider': 0, 'Gelir': 1900.0, 'Kart': 0, 'Tur': 'Gelir'})
    
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

    if date(year, month, 1) <= date(2026, 9, 19):
        items.append({'id': f'auto_enp_{month}', 'Tarih': date(year, month, 19), 'Kategori': 'Enpara Kr', 'Açıklama': 'Kredi', 'Gider': 23627.83, 'Gelir': 0, 'Kart': 0, 'Tur': 'Gider'})
    
    return pd.DataFrame(items)

# --- BAKİYE DEVİR HESAPLAYICI ---
def hesapla_devir(hedef_ay_idx):
    toplam_devir = 0.0
    for m in range(3, hedef_ay_idx): # Mart(3) ayından başla
        auto = get_monthly_recurring(2026, m)
        man = st.session_state.manual_data.copy()
        if not man.empty:
            man['Tarih'] = pd.to_datetime(man['Tarih']).dt.date
            man = man[pd.to_datetime(man['Tarih']).dt.month == m]
        
        ay_df = pd.concat([auto, man], ignore_index=True)
        # Eğer bir sabit ödeme manuel olarak değiştirilmişse, auto'dakini değil manueldeki tutarı al
        ay_df = ay_df.drop_duplicates(subset=['id'], keep='last')
        
        ay_fark = ay_df['Gelir'].sum() - ay_df['Gider'].sum() - ay_df['Kart'].sum()
        toplam_devir += ay_fark
    return toplam_devir

# --- ARAYÜZ ---
st.title("🏦 Kasa Pro v16.0")
secili_ay_ad = st.selectbox("İnceleme Ayı", TR_AYLAR, index=date.today().month - 1)
ay_idx = TR_AYLAR.index(secili_ay_ad) + 1

# Verileri çek ve birleştir
devir_tutari = hesapla_devir(ay_idx)
auto_df = get_monthly_recurring(2026, ay_idx)
man_df = st.session_state.manual_data.copy()

if not man_df.empty:
    man_df['Tarih'] = pd.to_datetime(man_df['Tarih']).dt.date
    man_df = man_df[pd.to_datetime(man_df['Tarih']).dt.month == ay_idx]

# Sabit ödemeleri manuel güncellemelerle ez (override)
full_df = pd.concat([auto_df, man_df], ignore_index=True)
full_df = full_df.drop_duplicates(subset=['id'], keep='last').sort_values('Tarih')

# Özet Paneli
c1, c2, c3, c4 = st.columns(4)
ay_gelir = full_df['Gelir'].sum()
ay_gider = full_df['Gider'].sum()
ay_kart = full_df['Kart'].sum()
net_toplam = devir_tutari + ay_gelir - ay_gider - ay_kart

c1.metric("Geçmişten Devir", f"{devir_tutari:,.2f} TL")
c2.metric("Bu Ay Gelir", f"{ay_gelir:,.2f} TL")
c3.metric("Bu Ay Gider", f"{(ay_gider + ay_kart):,.2f} TL")
c4.metric("Kasa Mevcudu", f"{net_toplam:,.2f} TL")

# --- TABLO FONKSİYONU ---
def tablo_olustur(df_subset, tur_label):
    if df_subset.empty:
        st.info(f"Kayıt yok.")
        return
    
    h1, h2, h3, h4 = st.columns([1, 2, 1, 1])
    h1.write("**Tarih**"); h2.write("**Açıklama**"); h3.write("**Tutar**"); h4.write("**İşlem**")

    for idx, row in df_subset.iterrows():
        c1, c2, c3, c4 = st.columns([1, 2, 1, 1])
        tutar = max(row['Gelir'], row['Gider'], row['Kart'])
        
        if st.session_state.edit_id == row['id']:
            with c2: e_acik = st.text_input("Açıklama", row['Açıklama'], key=f"e_a_{row['id']}")
            with c3: e_tut = st.number_input("Tutar", value=float(tutar), key=f"e_t_{row['id']}")
            with c4:
                if st.button("Kaydet ✅", key=f"s_{row['id']}"):
                    # Yeni bir manuel kayıt oluştur veya var olanı güncelle
                    new_row = {'id': row['id'], 'Tarih': row['Tarih'], 'Kategori': row['Kategori'], 'Açıklama': e_acik, 
                               'Gelir': e_tut if row['Tur'] == 'Gelir' else 0, 
                               'Gider': e_tut if row['Tur'] == 'Gider' else 0, 
                               'Kart': e_tut if row['Tur'] == 'Kredi Kartı' else 0, 'Tur': row['Tur']}
                    # Eski kaydı silip yenisini ekle
                    st.session_state.manual_data = st.session_state.manual_data[st.session_state.manual_data['id'] != row['id']]
                    st.session_state.manual_data = pd.concat([st.session_state.manual_data, pd.DataFrame([new_row])], ignore_index=True)
                    st.session_state.edit_id = None
                    st.rerun()
        else:
            c1.write(row['Tarih'].strftime('%d-%m'))
            c2.write(f"**{row['Kategori']}** - {row['Açıklama']}")
            c3.write(f"{tutar:,.2f} TL")
            with c4:
                e_btn, d_btn = st.columns(2)
                if e_btn.button("✏️", key=f"ed_{row['id']}"):
                    st.session_state.edit_id = row['id']
                    st.rerun()
                if d_btn.button("🗑️", key=f"dl_{row['id']}"):
                    st.session_state.manual_data = st.session_state.manual_data[st.session_state.manual_data['id'] != row['id']]
                    st.rerun()

# --- SEKMELER ---
t1, t2, t3 = st.tabs(["💰 Gelirler", "💸 Giderler", "💳 Kart"])
with t1: tablo_olustur(full_df[full_df['Tur'] == 'Gelir'], "G")
with t2: tablo_olustur(full_df[full_df['Tur'] == 'Gider'], "Gi")
with t3: tablo_olustur(full_df[full_df['Tur'] == 'Kredi Kartı'], "K")

# Yan Panel Girişi
with st.sidebar:
    st.header("➕ Yeni Harcama")
    with st.form("side_form", clear_on_submit=True):
        st.date_input("Tarih", date.today(), key="in_t")
        st.selectbox("Tür", ["Gelir", "Gider", "Kredi Kartı"], key="in_tr")
        st.selectbox("Kategori", ALT_KATEGORILER, key="in_k")
        st.text_input("Açıklama", key="in_a")
        st.number_input("Tutar", min_value=0.0, key="in_tut")
        if st.form_submit_button("Ekle"):
            nid = str(datetime.now().timestamp())
            nr = {'id': nid, 'Tarih': st.session_state.in_t, 'Kategori': st.session_state.in_k, 'Açıklama': st.session_state.in_a, 
                  'Gelir': st.session_state.in_tut if st.session_state.in_tr == 'Gelir' else 0,
                  'Gider': st.session_state.in_tut if st.session_state.in_tr == 'Gider' else 0,
                  'Kart': st.session_state.in_tut if st.session_state.in_tr == 'Kredi Kartı' else 0, 'Tur': st.session_state.in_tr}
            st.session_state.manual_data = pd.concat([st.session_state.manual_data, pd.DataFrame([nr])], ignore_index=True)
            st.rerun()
