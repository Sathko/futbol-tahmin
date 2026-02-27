import streamlit as st
sifre = st.text_input("🔐 Şifre girin", type="password")
if sifre != "felonjs1988":
    st.warning("Şifre gerekli.")
    st.stop()

import requests
import pandas as pd
import numpy as np
from scipy.stats import poisson
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="⚽ Oracle Futbol Tahmin", page_icon="⚽", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background-color: #0a0f1a; }
    h1, h2, h3 { color: #00d4ff; }
</style>
""", unsafe_allow_html=True)

API_KEY = "6f60cccb9ff5416e914f2955468a2df8"
RAPID_API_KEY = "65b1b84825msh9286bf99af17b2fp1b6a5bjsn918671af4a75"

ANA_LIGLER = {
    "PL":  "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "PD":  "La Liga 🇪🇸",
    "SA":  "Serie A 🇮🇹",
    "BL1": "Bundesliga 🇩🇪",
    "FL1": "Ligue 1 🇫🇷",
    "DED": "Eredivisie 🇳🇱",
    "PPL": "Primeira Liga 🇵🇹",
    "ELC": "Championship 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
}
AVRUPA_LIGLER = {
    "CL":  "Champions League 🇪🇺",
    "EL":  "Europa League 🇪🇺",
    "ECL": "Conference League 🇪🇺",
}
DIGER_LIGLER = {
    "BEL": "Belçika Pro League 🇧🇪",
    "NOR": "Norveç Eliteserien 🇳🇴",
    "ISV": "İsveç Allsvenskan 🇸🇪",
}
RAPID_ID_MAP = {"EL": "3", "ECL": "848", "BEL": "144", "NOR": "103", "ISV": "113"}

# ============================================================
# VERİ ÇEKME
# ============================================================
@st.cache_data(ttl=3600)
def mac_verisi_cek(lig_kodu):
    url = f"https://api.football-data.org/v4/competitions/{lig_kodu}/matches"
    headers = {"X-Auth-Token": API_KEY}
    params = {"season": "2024", "status": "FINISHED"}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        if r.status_code == 200:
            maclar = []
            for m in r.json().get("matches", []):
                if m["score"]["fullTime"]["home"] is not None:
                    maclar.append({
                        "ev_sahibi": m["homeTeam"]["name"],
                        "deplasman": m["awayTeam"]["name"],
                        "ev_gol": m["score"]["fullTime"]["home"],
                        "dep_gol": m["score"]["fullTime"]["away"],
                    })
            return pd.DataFrame(maclar)
    except:
        pass
    return pd.DataFrame()

@st.cache_data(ttl=1800)
def gelecek_maclar_cek(lig_kodu):
    url = f"https://api.football-data.org/v4/competitions/{lig_kodu}/matches"
    headers = {"X-Auth-Token": API_KEY}
    params = {"status": "SCHEDULED"}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        if r.status_code == 200:
            maclar = []
            for m in r.json().get("matches", [])[:20]:
                maclar.append({
                    "tarih": m["utcDate"][:10],
                    "saat": m["utcDate"][11:16] + " UTC",
                    "ev_sahibi": m["homeTeam"]["name"],
                    "deplasman": m["awayTeam"]["name"],
                })
            return pd.DataFrame(maclar)
    except:
        pass
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def rapid_mac_verisi_cek(rapid_id):
    url = "https://free-api-live-football-data.p.rapidapi.com/football-get-matches-by-league"
    headers = {"x-rapidapi-key": RAPID_API_KEY, "x-rapidapi-host": "free-api-live-football-data.p.rapidapi.com"}
    params = {"leagueid": rapid_id, "season": "2024"}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            matches = data.get("response", data.get("matches", data.get("data", [])))
            maclar = []
            for m in matches:
                try:
                    ev_gol = m.get("score", {}).get("fulltime", {}).get("home") or m.get("goals", {}).get("home")
                    dep_gol = m.get("score", {}).get("fulltime", {}).get("away") or m.get("goals", {}).get("away")
                    ev = m.get("teams", {}).get("home", {}).get("name") or m.get("homeTeam", {}).get("name", "")
                    dep = m.get("teams", {}).get("away", {}).get("name") or m.get("awayTeam", {}).get("name", "")
                    if ev_gol is not None and dep_gol is not None and ev and dep:
                        maclar.append({"ev_sahibi": ev, "deplasman": dep, "ev_gol": int(ev_gol), "dep_gol": int(dep_gol)})
                except:
                    continue
            return pd.DataFrame(maclar)
    except:
        pass
    return pd.DataFrame()

@st.cache_data(ttl=1800)
def rapid_gelecek_maclar_cek(rapid_id):
    url = "https://free-api-live-football-data.p.rapidapi.com/football-get-matches-by-league"
    headers = {"x-rapidapi-key": RAPID_API_KEY, "x-rapidapi-host": "free-api-live-football-data.p.rapidapi.com"}
    params = {"leagueid": rapid_id, "season": "2024"}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            matches = data.get("response", data.get("matches", data.get("data", [])))
            maclar = []
            for m in matches[:20]:
                try:
                    ev_gol = m.get("score", {}).get("fulltime", {}).get("home") or m.get("goals", {}).get("home")
                    if ev_gol is None:
                        ev = m.get("teams", {}).get("home", {}).get("name") or m.get("homeTeam", {}).get("name", "")
                        dep = m.get("teams", {}).get("away", {}).get("name") or m.get("awayTeam", {}).get("name", "")
                        tarih_raw = str(m.get("fixture", {}).get("date", m.get("date", "?")))
                        if ev and dep:
                            maclar.append({"tarih": tarih_raw[:10], "saat": tarih_raw[11:16] + " UTC" if len(tarih_raw) > 10 else "?", "ev_sahibi": ev, "deplasman": dep})
                except:
                    continue
            return pd.DataFrame(maclar)
    except:
        pass
    return pd.DataFrame()

# ============================================================
# MODEL
# ============================================================
def model_egit(df):
    if df.empty or len(df) < 10:
        return None, None
    lig_ort = df['ev_gol'].mean()
    takim_guc = {}
    for takim in set(df['ev_sahibi'].tolist() + df['deplasman'].tolist()):
        ev = df[df['ev_sahibi'] == takim]
        dep = df[df['deplasman'] == takim]
        takim_guc[takim] = {
            'attack': max(0.3, min(3.0, (((ev['ev_gol'].mean() if len(ev) > 0 else lig_ort) + (dep['dep_gol'].mean() if len(dep) > 0 else lig_ort)) / 2) / lig_ort)),
            'defense': max(0.3, min(3.0, (((ev['dep_gol'].mean() if len(ev) > 0 else lig_ort) + (dep['ev_gol'].mean() if len(dep) > 0 else lig_ort)) / 2) / lig_ort)),
        }
    return takim_guc, lig_ort

def tahmin_hesapla(ev_takim, dep_takim, takim_guc, lig_ort, ev_avantaji=1.25, ev_eksik=0, dep_eksik=0):
    if ev_takim not in takim_guc or dep_takim not in takim_guc:
        return None
    ev_bek = takim_guc[ev_takim]['attack'] * max(0.6, 1 - ev_eksik*0.04) * takim_guc[dep_takim]['defense'] * lig_ort * ev_avantaji
    dep_bek = takim_guc[dep_takim]['attack'] * max(0.6, 1 - dep_eksik*0.04) * takim_guc[ev_takim]['defense'] * lig_ort
    max_gol = 10
    matris = np.zeros((max_gol, max_gol))
    for i in range(max_gol):
        for j in range(max_gol):
            matris[i][j] = poisson.pmf(i, ev_bek) * poisson.pmf(j, dep_bek)

    p1 = float(np.sum(np.tril(matris, -1)))
    px = float(np.sum(np.diag(matris)))
    p2 = float(np.sum(np.triu(matris, 1)))

    # Gol marketleri
    alt25 = sum(matris[i][j] for i in range(max_gol) for j in range(max_gol) if i+j <= 2)
    alt35 = sum(matris[i][j] for i in range(max_gol) for j in range(max_gol) if i+j <= 3)
    alt45 = sum(matris[i][j] for i in range(max_gol) for j in range(max_gol) if i+j <= 4)
    alt55 = sum(matris[i][j] for i in range(max_gol) for j in range(max_gol) if i+j <= 5)

    kg_var = sum(matris[i][j] for i in range(1, max_gol) for j in range(1, max_gol))
    skorlar = sorted([(i, j, matris[i][j]) for i in range(max_gol) for j in range(max_gol)], key=lambda x: x[2], reverse=True)[:8]
    max_p = max(p1, px, p2)

    return {
        'ev_bek': round(ev_bek, 2), 'dep_bek': round(dep_bek, 2),
        'toplam_bek': round(ev_bek + dep_bek, 2),
        'p1': round(p1*100, 1), 'px': round(px*100, 1), 'p2': round(p2*100, 1),
        # 2.5
        'alt25': round(alt25*100, 1), 'ust25': round((1-alt25)*100, 1),
        'adil_ust25': round(1/(1-alt25), 2) if (1-alt25) > 0.01 else 99,
        'adil_alt25': round(1/alt25, 2) if alt25 > 0.01 else 99,
        # 3.5
        'alt35': round(alt35*100, 1), 'ust35': round((1-alt35)*100, 1),
        'adil_ust35': round(1/(1-alt35), 2) if (1-alt35) > 0.01 else 99,
        'adil_alt35': round(1/alt35, 2) if alt35 > 0.01 else 99,
        # 4.5
        'alt45': round(alt45*100, 1), 'ust45': round((1-alt45)*100, 1),
        'adil_ust45': round(1/(1-alt45), 2) if (1-alt45) > 0.01 else 99,
        'adil_alt45': round(1/alt45, 2) if alt45 > 0.01 else 99,
        # 5.5
        'alt55': round(alt55*100, 1), 'ust55': round((1-alt55)*100, 1),
        'adil_ust55': round(1/(1-alt55), 2) if (1-alt55) > 0.01 else 99,
        'adil_alt55': round(1/alt55, 2) if alt55 > 0.01 else 99,
        # diğer
        'kg_var': round(kg_var*100, 1), 'kg_yok': round((1-kg_var)*100, 1),
        'adil_1': round(1/p1, 2) if p1 > 0.01 else 99,
        'adil_x': round(1/px, 2) if px > 0.01 else 99,
        'adil_2': round(1/p2, 2) if p2 > 0.01 else 99,
        'guven': round(max_p*100, 1),
        'en_iyi': '1' if p1 == max_p else ('X' if px == max_p else '2'),
        'skorlar': skorlar,
    }

# ============================================================
# SIDEBAR
# ============================================================
st.title("⚽ ORACLE — Futbol Tahmin Sistemi")
st.markdown("*Poisson tabanlı istatistiksel tahmin motoru*")
st.divider()

with st.sidebar:
    st.header("⚙️ Ayarlar")
    lig_grubu = st.radio("Lig Grubu", ["Ana Ligler", "Avrupa Kupaları", "Diğer Ligler"])
    if lig_grubu == "Ana Ligler":
        lig_secenekler = ANA_LIGLER
    elif lig_grubu == "Avrupa Kupaları":
        lig_secenekler = AVRUPA_LIGLER
    else:
        lig_secenekler = DIGER_LIGLER
    secili_lig = st.selectbox("Lig Seç", list(lig_secenekler.keys()), format_func=lambda x: lig_secenekler[x])
    ev_avantaji = st.slider("Ev Sahibi Avantajı", 1.0, 1.6, 1.25, 0.05)
    min_guven = st.slider("Min. Güven Filtresi (%)", 40, 70, 50)
    st.divider()
    st.markdown("**Model:** Poisson Regresyon")
    st.markdown("**Güncelleme:** Her 1 saatte bir")

lig_adi = lig_secenekler[secili_lig]
is_rapid = secili_lig in RAPID_ID_MAP
rapid_id = RAPID_ID_MAP.get(secili_lig, "")

with st.spinner(f"{lig_adi} verileri yükleniyor..."):
    if is_rapid:
        df_gecmis = rapid_mac_verisi_cek(rapid_id)
        df_gelecek = rapid_gelecek_maclar_cek(rapid_id)
    else:
        df_gecmis = mac_verisi_cek(secili_lig)
        df_gelecek = gelecek_maclar_cek(secili_lig)
    takim_guc, lig_ort = model_egit(df_gecmis) if not df_gecmis.empty else (None, None)

if takim_guc is None:
    st.error("Veri yüklenemedi.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Eğitim Maçı", len(df_gecmis))
col2.metric("Takım Sayısı", len(takim_guc))
col3.metric("Yaklaşan Maç", len(df_gelecek))
col4.metric("Lig Ort. Gol", round(lig_ort, 2) if lig_ort else "—")
st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["📅 Haftalık Tahminler", "🔍 Maç Analizi", "💥 Gol Patlaması (4.5+)", "📊 Takım Güçleri"])

# ============================================================
# TAB 1 — HAFTALIK TAHMİNLER
# ============================================================
with tab1:
    st.subheader(f"Yaklaşan Maçlar — {lig_adi}")
    if df_gelecek.empty:
        st.info("Bu lig için yaklaşan maç bulunamadı.")
    else:
        tahminler = []
        for _, mac in df_gelecek.iterrows():
            t = tahmin_hesapla(mac['ev_sahibi'], mac['deplasman'], takim_guc, lig_ort, ev_avantaji)
            if t:
                tahminler.append({
                    'Tarih': mac['tarih'], 'Saat': mac['saat'],
                    'Ev Sahibi': mac['ev_sahibi'], 'Deplasman': mac['deplasman'],
                    '1 %': t['p1'], 'X %': t['px'], '2 %': t['p2'],
                    'Üst2.5 %': t['ust25'], 'Üst3.5 %': t['ust35'],
                    'Üst4.5 %': t['ust45'],
                    'KG Var %': t['kg_var'],
                    'Adil 1': t['adil_1'], 'Adil X': t['adil_x'], 'Adil 2': t['adil_2'],
                    'Adil Üst2.5': t['adil_ust25'],
                    'Adil Üst3.5': t['adil_ust35'],
                    'Adil Üst4.5': t['adil_ust45'],
                    'Güven %': t['guven'], 'Öneri': t['en_iyi'],
                })
        if tahminler:
            df_t = pd.DataFrame(tahminler)
            df_t = df_t[df_t['Güven %'] >= min_guven].sort_values('Güven %', ascending=False)
            if df_t.empty:
                st.warning("Güven eşiğini düşür.")
            else:
                yuksek = df_t[df_t['Güven %'] >= 55]
                if not yuksek.empty:
                    st.success(f"🔥 {len(yuksek)} YÜKSEK GÜVEN MAÇ bulundu!")
                    for _, r in yuksek.iterrows():
                        c1, c2, c3, c4 = st.columns([2, 1, 2, 2])
                        c1.markdown(f"**{r['Ev Sahibi']}**")
                        c2.markdown(f"<div style='text-align:center;color:#888'>{r['Tarih']}</div>", unsafe_allow_html=True)
                        c3.markdown(f"**{r['Deplasman']}**")
                        c4.markdown(f"✅ Öneri: **{r['Öneri']}** | Güven: **{r['Güven %']}%**")
                st.divider()
                st.dataframe(df_t, use_container_width=True, hide_index=True,
                             column_config={'Güven %': st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d%%")})
                csv = df_t.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 CSV İndir", csv, "tahminler.csv", "text/csv")

# ============================================================
# TAB 2 — MAÇ ANALİZİ
# ============================================================
with tab2:
    st.subheader("Detaylı Maç Analizi")
    takimlar = sorted(list(takim_guc.keys()))
    col1, col2 = st.columns(2)
    ev_sec = col1.selectbox("Ev Sahibi", takimlar)
    dep_sec = col2.selectbox("Deplasman", [t for t in takimlar if t != ev_sec])
    col3, col4 = st.columns(2)
    ev_eksik = col3.number_input("Ev Sahibi Eksik Oyuncu", min_value=0, max_value=11, value=0)
    dep_eksik = col4.number_input("Deplasman Eksik Oyuncu", min_value=0, max_value=11, value=0)

    if st.button("🔮 Tahmin Yap", type="primary"):
        t = tahmin_hesapla(ev_sec, dep_sec, takim_guc, lig_ort, ev_avantaji, ev_eksik, dep_eksik)
        if t:
            st.divider()
            c1, c2, c3 = st.columns(3)
            c1.metric(f"{ev_sec[:20]} Bek. Gol", t['ev_bek'])
            c2.metric(f"{dep_sec[:20]} Bek. Gol", t['dep_bek'])
            c3.metric("Toplam Bek. Gol", t['toplam_bek'])
            st.divider()

            st.markdown("#### 1 / X / 2")
            c1, c2, c3 = st.columns(3)
            c1.metric("1 — Ev Kazanır", f"%{t['p1']}", f"Adil Oran: {t['adil_1']}")
            c2.metric("X — Beraberlik", f"%{t['px']}", f"Adil Oran: {t['adil_x']}")
            c3.metric("2 — Dep Kazanır", f"%{t['p2']}", f"Adil Oran: {t['adil_2']}")

            st.markdown("#### Gol Marketleri — Tüm Eşikler")
            gol_data = {
                'Market': ['Üst 2.5', 'Alt 2.5', 'Üst 3.5', 'Alt 3.5', 'Üst 4.5', 'Alt 4.5', 'Üst 5.5', 'Alt 5.5', 'KG Var', 'KG Yok'],
                'İhtimal %': [t['ust25'], t['alt25'], t['ust35'], t['alt35'], t['ust45'], t['alt45'], t['ust55'], t['alt55'], t['kg_var'], t['kg_yok']],
                'Adil Oran': [t['adil_ust25'], t['adil_alt25'], t['adil_ust35'], t['adil_alt35'], t['adil_ust45'], t['adil_alt45'], t['adil_ust55'], t['adil_alt55'], round(1/(t['kg_var']/100),2) if t['kg_var'] > 1 else 99, round(1/(t['kg_yok']/100),2) if t['kg_yok'] > 1 else 99],
            }
            gol_df = pd.DataFrame(gol_data)
            st.dataframe(gol_df, hide_index=True, use_container_width=True,
                         column_config={'İhtimal %': st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%")})

            st.markdown("#### En Olası Skorlar")
            skor_df = pd.DataFrame(t['skorlar'], columns=['Ev Golü', 'Dep Golü', 'Olasılık'])
            skor_df['Skor'] = skor_df['Ev Golü'].astype(str) + " - " + skor_df['Dep Golü'].astype(str)
            skor_df['Toplam Gol'] = skor_df['Ev Golü'] + skor_df['Dep Golü']
            skor_df['Olasılık %'] = skor_df['Olasılık'].apply(lambda x: f"%{round(x*100, 1)}")
            st.dataframe(skor_df[['Skor', 'Toplam Gol', 'Olasılık %']], hide_index=True)

            guven_renk = "🔥" if t['guven'] >= 55 else ("⚡" if t['guven'] >= 45 else "❌")
            st.info(f"{guven_renk} **ÖNERİ:** {t['en_iyi']} seçeneği ({t['guven']}% güven)")

# ============================================================
# TAB 3 — GOL PATLAMASI
# ============================================================
with tab3:
    st.subheader("💥 Gol Patlaması — 4.5 Üst Sıralaması")
    st.markdown("Bu sekme, **en yüksek gol potansiyelli** maçları sıralar. 4.5 üst oynayacaksan buraya bak.")

    if df_gelecek.empty:
        st.info("Bu lig için yaklaşan maç bulunamadı.")
    else:
        gol_tahminler = []
        for _, mac in df_gelecek.iterrows():
            t = tahmin_hesapla(mac['ev_sahibi'], mac['deplasman'], takim_guc, lig_ort, ev_avantaji)
            if t:
                gol_tahminler.append({
                    'Tarih': mac['tarih'],
                    'Ev Sahibi': mac['ev_sahibi'],
                    'Deplasman': mac['deplasman'],
                    'Bek. Toplam Gol': t['toplam_bek'],
                    'Üst 2.5 %': t['ust25'],
                    'Üst 3.5 %': t['ust35'],
                    'Üst 4.5 %': t['ust45'],
                    'Üst 5.5 %': t['ust55'],
                    'Adil Üst2.5': t['adil_ust25'],
                    'Adil Üst3.5': t['adil_ust35'],
                    'Adil Üst4.5': t['adil_ust45'],
                    'Adil Üst5.5': t['adil_ust55'],
                    'KG Var %': t['kg_var'],
                })

        if gol_tahminler:
            df_gol = pd.DataFrame(gol_tahminler).sort_values('Üst 4.5 %', ascending=False)

            # En yüksek 4.5 üst ihtimalli maçları vurgula
            top3 = df_gol.head(3)
            st.markdown("#### 🔥 En Yüksek Gol Potansiyelli 3 Maç")
            for _, r in top3.iterrows():
                with st.container():
                    c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
                    c1.markdown(f"**{r['Ev Sahibi']}** vs **{r['Deplasman']}** — {r['Tarih']}")
                    c2.metric("Bek. Gol", r['Bek. Toplam Gol'])
                    c3.metric("4.5 Üst %", f"%{r['Üst 4.5 %']}")
                    c4.metric("Adil Oran", r['Adil Üst4.5'])

            st.divider()
            st.markdown("#### Tüm Maçlar — Gol Marketleri")

            # Eşik seçici
            esik = st.select_slider("Gösterilecek Minimum Üst 4.5 İhtimali (%)", options=[5, 10, 15, 20, 25, 30], value=10)
            df_gol_filtre = df_gol[df_gol['Üst 4.5 %'] >= esik]

            if df_gol_filtre.empty:
                st.warning(f"Bu ligde %{esik} üzeri 4.5 üst ihtimali olan maç yok. Eşiği düşür.")
            else:
                st.dataframe(
                    df_gol_filtre,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'Üst 2.5 %': st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%"),
                        'Üst 3.5 %': st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%"),
                        'Üst 4.5 %': st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%"),
                        'Üst 5.5 %': st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%"),
                    }
                )

            st.divider()
            st.markdown("#### 💡 Nasıl Kullanılır?")
            st.info("""
**Adil Oran** = Sistemin hesapladığı gerçek değer.
**Nesine oranı > Adil Oran** ise → Value bet ✅

Örnek:
- Sistem Üst 4.5 Adil Oran: **4.20**
- Nesine Üst 4.5 veriyor: **5.50**
- 5.50 > 4.20 → **Oyna!** ✅

4.5 üst nadiren gerçekleşir (%15-30) ama oranlar yüksek olur (3.50-8.00).
Value bulursan uzun vadede en karlı marketlerden biridir.
            """)

# ============================================================
# TAB 4 — TAKIM GÜÇLERİ
# ============================================================
with tab4:
    st.subheader("Takım Güç Sıralaması")
    guc_df = pd.DataFrame([
        {'Takım': k, 'Saldırı Gücü': round(v['attack'], 3), 'Savunma Zayıflığı': round(v['defense'], 3)}
        for k, v in takim_guc.items()
    ]).sort_values('Saldırı Gücü', ascending=False)
    guc_df.insert(0, 'Sıra', range(1, len(guc_df)+1))
    st.markdown("*Saldırı Gücü > 1.0 = ligden iyi. Savunma Zayıflığı < 1.0 = iyi savunma.*")
    st.dataframe(guc_df, use_container_width=True, hide_index=True,
                 column_config={
                     'Saldırı Gücü': st.column_config.ProgressColumn(min_value=0, max_value=2.5, format="%.2f"),
                     'Savunma Zayıflığı': st.column_config.ProgressColumn(min_value=0, max_value=2.5, format="%.2f"),
                 })

st.divider()
st.caption("⚠️ Bu sistem istatistiksel tahmin üretir. Bahis bağımlılığı risk taşır. Sorumlu oynayın.")
