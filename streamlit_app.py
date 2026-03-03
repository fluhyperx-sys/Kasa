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
    import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar

# --- AYARLAR VE TASARIM ---
st.set_page_config(page_title="Kasa Pro v11.0", layout="wide")

# --- VERİ SAKLAMA (SESSION STATE) ---
if 'data' not in st.session_state:
    # 1 Mart 2026'dan itibaren sabit verileri sisteme bir kez tanımlıyoruz
    initial_data = [
        # DÜZENLİ GELİRLER
        {'Tarih': date(2026, 3, 2), 'Kategori': 'Maaş', 'Açıklama': 'Düzenli Maaş', 'Gelir': 37555.07, 'Gider': 0, 'Kart': 0, 'Tur': 'Gelir', 'Sabit': True},
        {'Tarih': date(2026, 3, 2), 'Kategori': 'Elden', 'Açıklama': 'Düzenli Elden', 'Gelir': 30640.00, 'Gider': 0, 'Kart': 0, 'Tur': 'Gelir', 'Sabit': True},
        {'Tarih': date(2026, 3, 1), 'Kategori': 'Yemek', 'Açıklama': 'Yemek Kartı 1', 'Gelir': 3200.00, 'Gider': 0, 'Kart': 0, 'Tur': 'Gelir', 'Sabit': True},
        {'Tarih': date(2026, 3, 15), 'Kategori': 'Yemek', 'Açıklama': 'Yemek Kartı 2', 'Gelir': 3000.00, 'Gider': 0, 'Kart': 0, 'Tur': 'Gelir', 'Sabit': True},
        # DÜZENLİ GİDERLER
        {'Tarih': date(2026, 3, 5), 'Kategori': 'Sheri BES', 'Açıklama': 'Bireysel Emeklilik', 'Gelir': 0, 'Gider': 2000.00, 'Kart': 0, 'Tur': 'Gider', 'Sabit': True},
        {'Tarih': date(2026, 3, 5), 'Kategori': 'Batu TEL', 'Açıklama': 'Telefon Faturası', 'Gelir': 0, 'Gider': 810.75, 'Kart': 0, 'Tur': 'Gider', 'Sabit': True},
        {'Tarih': date(2026, 3, 5), 'Kategori': 'Garanti KK', 'Açıklama': 'Kredi Kartı Ödemesi', 'Gelir': 0, 'Gider': 37000.00, 'Kart': 0, 'Tur': 'Gider', 'Sabit': True},
        {'Tarih': date(2026, 3, 15), 'Kategori': 'İski SU', 'Açıklama': 'Su Faturası', 'Gelir': 0, 'Gider': 750.00, 'Kart': 0, 'Tur': 'Gider', 'Sabit': True},
        {'Tarih': date(2026, 3, 15), 'Kategori': 'Sheri TEL', 'Açıklama': 'Telefon Faturası', 'Gelir': 0, 'Gider': 431.00, 'Kart': 0, 'Tur': 'Gider', 'Sabit': True},
        {'Tarih': date(2026, 3, 15), 'Kategori': 'İgdaş Doğal Gaz', 'Açıklama': 'Doğal Gaz', 'Gelir': 0, 'Gider': 2500.00, 'Kart': 0, 'Tur': 'Gider', 'Sabit': True},
        {'Tarih': date(2026, 3, 19), 'Kategori': 'Enpara Kr', 'Açıklama': 'Kredi Taksidi (Eylül Son)', 'Gelir': 0, 'Gider': 23627.83, 'Kart': 0, 'Tur': 'Gider', 'Sabit': True},
    ]
    st.session_state.data = pd.DataFrame(initial_data)

# --- FONKSİYONLAR ---
def veri_ekle(tarih, kategori, aciklama, tutar, tur):
    # Mükerrer kontrolü (Aynı gün, aynı kategori ve aynı tutar varsa ekleme)
    is_duplicate = not st.session_state.data[
        (st.session_state.data['Tarih'] == tarih) & 
        (st.session_state.data['Kategori'] == kategori) & 
        ((st.session_state.data['Gelir'] == tutar) | (st.session_state.data['Gider'] == tutar) | (st.session_state.data['Kart'] == tutar))
    ].empty
    
    if is_duplicate:
        st.warning("Bu kayıt zaten mevcut (Mükerrer Engellendi).")
    else:
        yeni = {
            'Tarih': tarih, 'Kategori': kategori, 'Açıklama': aciklama,
            'Gelir': tutar if tur == 'Gelir' else 0,
            'Gider': tutar if tur == 'Gider' else 0,
            'Kart': tutar if tur == 'Kredi Kartı' else 0,
            'Tur': tur, 'Sabit': False
        }
        st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([yeni])], ignore_index=True)
        st.success("İşlem Kaydedildi.")

# --- ARAYÜZ ---
st.title("💰 Profesyonel Kasa ve Bütçe Takibi")

# Sol Panel - Veri Girişi
with st.sidebar:
    st.header("➕ İşlem Ekle")
    f_tarih = st.date_input("Tarih", date.today())
    f_tur = st.selectbox("Tür", ["Gelir", "Gider", "Kredi Kartı"])
    f_kat = st.selectbox("Kategori", ["Maaş", "Elden", "Haftalık", "Yemek", "Emekli Maaş", "Pazar Gideri", "Fatura", "Kredi", "Diğer"])
    f_aciklama = st.text_input("Açıklama")
    f_tutar = st.number_input("Tutar", min_value=0.0, step=10.0)
    
    if st.button("Kaydet"):
        veri_ekle(f_tarih, f_kat, f_aciklama, f_tutar, f_tur)

# Üst Panel - Ay Seçimi
aylar = list(calendar.month_name)[1:]
secili_ay_ad = st.selectbox("Görüntülenen Ay", aylar, index=date.today().month - 1)
ay_no = aylar.index(secili_ay_ad) + 1

# Veriyi Filtrele (1 Mart 2026 ve sonrası)
df = st.session_state.data.copy()
df['Tarih'] = pd.to_datetime(df['Tarih'])
# Enpara Kr kontrolü (Eylül 2026 sonrası gösterme)
df = df[~((df['Kategori'] == 'Enpara Kr') & (df['Tarih'] > pd.Timestamp(2026, 9, 20)))]
aylik_df = df[df['Tarih'].dt.month == ay_no]

# --- SEKMLER ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Genel Durum", "📈 Gelirler", "📉 Giderler", "💳 Kredi Kartı Takibi"])

with tab1:
    col1, col2, col3 = st.columns(3)
    gelir_top = aylik_df['Gelir'].sum()
    gider_top = aylik_df['Gider'].sum()
    kart_top = aylik_df['Kart'].sum()
    
    col1.metric("Toplam Gelir", f"{gelir_top:,.2f} TL")
    col2.metric("Nakit Gider", f"{gider_top:,.2f} TL")
    col3.metric("Kart Harcaması", f"{kart_top:,.2f} TL")
    st.divider()
    st.subheader("Tüm İşlem Geçmişi")
    st.write("Buradan kayıtları kontrol edebilir veya silebilirsiniz.")
    
    # Silme İşlemi İçin Liste
    for i, row in aylik_df.iterrows():
        c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
        c1.write(f"{row['Tarih'].strftime('%d-%m-%Y')} | {row['Kategori']}")
        c2.write(f"{row['Açıklama']}")
        c3.write(f"{max(row['Gelir'], row['Gider'], row['Kart']):,.2f} TL")
        if c4.button("Sil", key=f"del_{i}"):
            st.session_state.data = st.session_state.data.drop(i)
            st.rerun()

with tab2:
    st.subheader("Aylık Gelir Tablosu")
    st.dataframe(aylik_df[aylik_df['Tur'] == 'Gelir'][['Tarih', 'Kategori', 'Açıklama', 'Gelir']], use_container_width=True)

with tab3:
    st.subheader("Aylık Nakit Gider Tablosu")
    st.dataframe(aylik_df[aylik_df['Tur'] == 'Gider'][['Tarih', 'Kategori', 'Açıklama', 'Gider']], use_container_width=True)

with tab4:
    st.subheader("💳 Kredi Kartı ve İleri Tarihli Borçlar")
