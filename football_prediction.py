# ============================================================
# ORACLE FUTBOL TAHMİN SİSTEMİ
# Google Colab'da çalıştır — hiç kod bilmene gerek yok
# ============================================================

# ADIM 1: Gerekli kütüphaneleri yükle
# Colab'da ilk hücreye bunu yapıştır ve çalıştır

INSTALL_CODE = """
!pip install requests pandas numpy scipy streamlit pyngrok -q
"""

# ADIM 2: ANA SİSTEM KODU
# İkinci hücreye bunu yapıştır

MAIN_CODE = """
import requests
import pandas as pd
import numpy as np
from scipy.stats import poisson
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# AYARLAR — Sadece bu kısmı değiştir
# ============================================================
API_KEY = "6f60cccb9ff5416e914f2955468a2df8"  # football-data.org API key

# Ligler — kod : isim
LIGLER = {
    "PL":  "Premier League",
    "PD":  "La Liga", 
    "SA":  "Serie A",
    "BL1": "Bundesliga",
    "FL1": "Ligue 1",
    "CL":  "Champions League",
}
# Süper Lig için ayrı kaynak kullanıyoruz (aşağıda)

# ============================================================
# VERİ ÇEKME
# ============================================================

def mac_verisi_cek(lig_kodu, sezon="2024"):
    \"""Son maçları çek\"""
    url = f"https://api.football-data.org/v4/competitions/{lig_kodu}/matches"
    headers = {"X-Auth-Token": API_KEY}
    params = {"season": sezon, "status": "FINISHED"}
    
    try:
        r = requests.get(url, headers=headers, params=params)
        if r.status_code == 200:
            data = r.json()
            maclar = []
            for m in data.get("matches", []):
                if m["score"]["fullTime"]["home"] is not None:
                    maclar.append({
                        "tarih": m["utcDate"][:10],
                        "ev_sahibi": m["homeTeam"]["name"],
                        "deplasman": m["awayTeam"]["name"],
                        "ev_gol": m["score"]["fullTime"]["home"],
                        "dep_gol": m["score"]["fullTime"]["away"],
                    })
            return pd.DataFrame(maclar)
        else:
            print(f"Hata {lig_kodu}: {r.status_code}")
            return pd.DataFrame()
    except Exception as e:
        print(f"Bağlantı hatası: {e}")
        return pd.DataFrame()

def gelecek_maclar_cek(lig_kodu):
    \"""Bu haftanın maçlarını çek\"""
    url = f"https://api.football-data.org/v4/competitions/{lig_kodu}/matches"
    headers = {"X-Auth-Token": API_KEY}
    params = {"status": "SCHEDULED"}
    
    try:
        r = requests.get(url, headers=headers, params=params)
        if r.status_code == 200:
            data = r.json()
            maclar = []
            for m in data.get("matches", [])[:20]:  # İlk 20 maç
                maclar.append({
                    "tarih": m["utcDate"][:10],
                    "saat": m["utcDate"][11:16],
                    "ev_sahibi": m["homeTeam"]["name"],
                    "deplasman": m["awayTeam"]["name"],
                    "lig": LIGLER.get(lig_kodu, lig_kodu),
                })
            return pd.DataFrame(maclar)
        else:
            return pd.DataFrame()
    except:
        return pd.DataFrame()

# ============================================================
# POİSSON TAHMİN MOTORu
# ============================================================

class PoissonTahminMotoru:
    def __init__(self):
        self.takim_guc = {}      # Her takımın attack/defense gücü
        self.ev_avantaji = 1.25  # Ev sahibi avantaj katsayısı
        self.hazir = False
        
    def egit(self, df):
        \"""Geçmiş maçlarla modeli eğit\"""
        if df.empty or len(df) < 20:
            print("Yeterli veri yok")
            return False
            
        takimlar = list(set(df['ev_sahibi'].tolist() + df['deplasman'].tolist()))
        
        # Her takım için attack ve defense gücü hesapla
        lig_ort_gol = df['ev_gol'].mean()
        
        for takim in takimlar:
            ev_maclar = df[df['ev_sahibi'] == takim]
            dep_maclar = df[df['deplasman'] == takim]
            
            # Attack strength = takımın gol ortalaması / lig ortalaması
            ev_atilan = ev_maclar['ev_gol'].mean() if len(ev_maclar) > 0 else lig_ort_gol
            dep_atilan = dep_maclar['dep_gol'].mean() if len(dep_maclar) > 0 else lig_ort_gol
            attack = (ev_atilan + dep_atilan) / 2 / lig_ort_gol
            
            # Defense weakness = takıma atılan goller / lig ortalaması
            ev_yenilen = ev_maclar['dep_gol'].mean() if len(ev_maclar) > 0 else lig_ort_gol
            dep_yenilen = dep_maclar['ev_gol'].mean() if len(dep_maclar) > 0 else lig_ort_gol
            defense = (ev_yenilen + dep_yenilen) / 2 / lig_ort_gol
            
            self.takim_guc[takim] = {
                'attack': max(0.3, min(3.0, attack)),
                'defense': max(0.3, min(3.0, defense)),
                'mac_sayisi': len(ev_maclar) + len(dep_maclar)
            }
        
        self.lig_ort_gol = lig_ort_gol
        self.hazir = True
        return True
    
    def beklenen_gol(self, ev_takim, dep_takim):
        \"""Her takımın beklenen gol sayısını hesapla\"""
        if ev_takim not in self.takim_guc:
            return self.lig_ort_gol * self.ev_avantaji, self.lig_ort_gol
        if dep_takim not in self.takim_guc:
            return self.lig_ort_gol * self.ev_avantaji, self.lig_ort_gol
            
        ev_guc = self.takim_guc[ev_takim]
        dep_guc = self.takim_guc[dep_takim]
        
        # Ev sahibi beklenen gol
        ev_beklenen = (ev_guc['attack'] * dep_guc['defense'] * 
                       self.lig_ort_gol * self.ev_avantaji)
        
        # Deplasman beklenen gol  
        dep_beklenen = (dep_guc['attack'] * ev_guc['defense'] * 
                        self.lig_ort_gol)
        
        return round(ev_beklenen, 3), round(dep_beklenen, 3)
    
    def olasilik_hesapla(self, ev_takim, dep_takim, max_gol=6):
        \"""Tüm skorların olasılık matrisini hesapla\"""
        ev_bek, dep_bek = self.beklenen_gol(ev_takim, dep_takim)
        
        # Poisson dağılımı ile skor matrisi
        matris = np.zeros((max_gol+1, max_gol+1))
        for i in range(max_gol+1):
            for j in range(max_gol+1):
                matris[i][j] = poisson.pmf(i, ev_bek) * poisson.pmf(j, dep_bek)
        
        # 1/X/2 olasılıkları
        ev_kazanir = np.sum(np.tril(matris, -1))   # alt üçgen
        beraberlik = np.sum(np.diag(matris))        # köşegen
        dep_kazanir = np.sum(np.triu(matris, 1))    # üst üçgen
        
        # Alt/Üst 2.5
        alt_25 = sum(matris[i][j] for i in range(max_gol+1) 
                     for j in range(max_gol+1) if i+j <= 2)
        ust_25 = 1 - alt_25
        
        # Her iki takım gol atar (KG: Var)
        kg_var = sum(matris[i][j] for i in range(1, max_gol+1) 
                     for j in range(1, max_gol+1))
        
        # En olası skorlar
        skorlar = []
        for i in range(max_gol+1):
            for j in range(max_gol+1):
                skorlar.append((i, j, matris[i][j]))
        skorlar.sort(key=lambda x: x[2], reverse=True)
        
        return {
            'ev_beklenen_gol': ev_bek,
            'dep_beklenen_gol': dep_bek,
            'ev_kazanma': round(ev_kazanir * 100, 1),
            'beraberlik': round(beraberlik * 100, 1),
            'dep_kazanma': round(dep_kazanir * 100, 1),
            'alt_25': round(alt_25 * 100, 1),
            'ust_25': round(ust_25 * 100, 1),
            'kg_var': round(kg_var * 100, 1),
            'kg_yok': round((1-kg_var) * 100, 1),
            'en_olasi_skorlar': skorlar[:5],
        }
    
    def value_bet_hesapla(self, olasiliklar, iddaa_oranlari=None):
        \"""Value bet tespiti: bizim olasılığımız > oran olasılığından büyükse value var\"""
        sonuclar = {}
        
        p1 = olasiliklar['ev_kazanma'] / 100
        px = olasiliklar['beraberlik'] / 100
        p2 = olasiliklar['dep_kazanma'] / 100
        
        # Önerilen oran (adil oran = 1/olasılık, margin ekle)
        sonuclar['adil_oran_1'] = round(1/p1, 2) if p1 > 0 else 99
        sonuclar['adil_oran_X'] = round(1/px, 2) if px > 0 else 99
        sonuclar['adil_oran_2'] = round(1/p2, 2) if p2 > 0 else 99
        
        # Güven skoru: olasılıkların ne kadar ayrışık olduğu
        max_p = max(p1, px, p2)
        if max_p > 0.55:
            guven = "YÜKSEK 🔥"
        elif max_p > 0.45:
            guven = "ORTA ⚡"
        else:
            guven = "DÜŞÜK — ATLA ❌"
        
        sonuclar['guven'] = guven
        sonuclar['guven_yuzde'] = round(max_p * 100, 1)
        
        # En iyi bahis önerisi
        if p1 == max_p:
            sonuclar['oneri'] = f"1 (Ev Sahibi) — {round(p1*100,1)}%"
        elif px == max_p:
            sonuclar['oneri'] = f"X (Beraberlik) — {round(px*100,1)}%"
        else:
            sonuclar['oneri'] = f"2 (Deplasman) — {round(p2*100,1)}%"
            
        return sonuclar

# ============================================================
# ANA TAHMİN FONKSİYONU
# ============================================================

def tahmin_yap(ev_takim, dep_takim, motor):
    \"""Tek maç için tam analiz\"""
    if not motor.hazir:
        return None
    
    olasilikar = motor.olasilik_hesapla(ev_takim, dep_takim)
    value = motor.value_bet_hesapla(olasilikar)
    
    print(f"\\n{'='*60}")
    print(f"  {ev_takim} vs {dep_takim}")
    print(f"{'='*60}")
    print(f"  Beklenen gol: {ev_takim[:15]}: {olasilikar['ev_beklenen_gol']}  |  {dep_takim[:15]}: {olasilikar['dep_beklenen_gol']}")
    print(f"{'─'*60}")
    print(f"  1 (Ev):  %{olasilikar['ev_kazanma']}   →  Adil oran: {value['adil_oran_1']}")
    print(f"  X (Ber): %{olasilikar['beraberlik']}   →  Adil oran: {value['adil_oran_X']}")
    print(f"  2 (Dep): %{olasilikar['dep_kazanma']}   →  Adil oran: {value['adil_oran_2']}")
    print(f"{'─'*60}")
    print(f"  Alt 2.5: %{olasilikar['alt_25']}  |  Üst 2.5: %{olasilikar['ust_25']}")
    print(f"  KG Var:  %{olasilikar['kg_var']}   |  KG Yok:  %{olasilikar['kg_yok']}")
    print(f"{'─'*60}")
    print(f"  En olası skorlar:")
    for skor in olasilikar['en_olasi_skorlar']:
        print(f"    {skor[0]}-{skor[1]} : %{round(skor[2]*100,1)}")
    print(f"{'─'*60}")
    print(f"  ★ ÖNERİ: {value['oneri']}")
    print(f"  ★ GÜVEN: {value['guven']} ({value['guven_yuzde']}%)")
    print(f"{'='*60}")
    
    return {**olasilikar, **value}

# ============================================================
# HAFTALIK TAHMİN RAPORU
# ============================================================

def haftalik_rapor():
    \"""Tüm ligler için bu haftanın tahminleri\"""
    
    print("\\n🔄 Veriler çekiliyor...")
    
    tum_motorlar = {}
    tum_gelecek = []
    
    for lig_kodu, lig_adi in LIGLER.items():
        print(f"  → {lig_adi} yükleniyor...")
        
        # Geçmiş maçları çek ve modeli eğit
        df = mac_verisi_cek(lig_kodu)
        if not df.empty:
            motor = PoissonTahminMotoru()
            motor.egit(df)
            tum_motorlar[lig_kodu] = motor
            
            # Gelecek maçları çek
            gelecek = gelecek_maclar_cek(lig_kodu)
            if not gelecek.empty:
                gelecek['lig_kodu'] = lig_kodu
                tum_gelecek.append(gelecek)
    
    if not tum_gelecek:
        print("Bu hafta programlanmış maç bulunamadı.")
        return
    
    tum_gelecek_df = pd.concat(tum_gelecek, ignore_index=True)
    
    print(f"\\n✅ {len(tum_gelecek_df)} maç bulundu. Tahminler hesaplanıyor...\\n")
    
    # Her maç için tahmin
    tum_tahminler = []
    
    for _, mac in tum_gelecek_df.iterrows():
        lig_kodu = mac['lig_kodu']
        if lig_kodu not in tum_motorlar:
            continue
            
        motor = tum_motorlar[lig_kodu]
        ev = mac['ev_sahibi']
        dep = mac['deplasman']
        
        if ev not in motor.takim_guc or dep not in motor.takim_guc:
            continue
        
        olasilikar = motor.olasilik_hesapla(ev, dep)
        value = motor.value_bet_hesapla(olasilikar)
        
        tum_tahminler.append({
            'Tarih': mac['tarih'],
            'Saat': mac.get('saat', '?'),
            'Lig': mac['lig'],
            'Ev Sahibi': ev,
            'Deplasman': dep,
            'Ev%': olasilikar['ev_kazanma'],
            'Ber%': olasilikar['beraberlik'],
            'Dep%': olasilikar['dep_kazanma'],
            'Üst2.5%': olasilikar['ust_25'],
            'KGVar%': olasilikar['kg_var'],
            'Öneri': value['oneri'],
            'Güven': value['guven'],
            'Güven%': value['guven_yuzde'],
        })
    
    # DataFrame yap ve göster
    if tum_tahminler:
        df_sonuc = pd.DataFrame(tum_tahminler)
        df_sonuc = df_sonuc.sort_values(['Güven%', 'Tarih'], ascending=[False, True])
        
        print("\\n" + "="*80)
        print("  📊 HAFTALIK TAHMİN RAPORU")
        print("="*80)
        
        # Sadece yüksek güvenli maçları öne çıkar
        yuksek = df_sonuc[df_sonuc['Güven%'] >= 55]
        print(f"\\n🔥 YÜKSEK GÜVEN ({len(yuksek)} maç):")
        if not yuksek.empty:
            print(yuksek[['Tarih','Lig','Ev Sahibi','Deplasman','Öneri','Güven']].to_string(index=False))
        
        print(f"\\n⚡ TÜM TAHMİNLER ({len(df_sonuc)} maç):")
        print(df_sonuc[['Tarih','Saat','Lig','Ev Sahibi','Deplasman','Ev%','Ber%','Dep%','Üst2.5%','KGVar%','Güven']].to_string(index=False))
        
        # CSV'ye kaydet
        df_sonuc.to_csv('tahminler.csv', index=False, encoding='utf-8-sig')
        print("\\n✅ tahminler.csv dosyasına kaydedildi!")
        
        return df_sonuc
    else:
        print("Tahmin üretilemedi.")
        return None

# ============================================================
# ÇALIŞTIR
# ============================================================
print("⚽ ORACLE Futbol Tahmin Sistemi başlatılıyor...")
print("="*50)

# Haftalık rapor üret
rapor = haftalik_rapor()

# Manuel tek maç tahmini için:
# Önce motor oluştur:
# df = mac_verisi_cek("PL")
# motor = PoissonTahminMotoru()
# motor.egit(df)
# tahmin_yap("Arsenal FC", "Chelsea FC", motor)
"""

print("Kod hazır!")
print("Aşağıdaki adımları izle:")
print("1. colab.research.google.com aç")
print("2. New Notebook oluştur")
print("3. Kodu yapıştır ve Run All bas")
