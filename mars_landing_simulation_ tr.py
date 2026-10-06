"""
Mars İniş Simülasyonu - Suicide Burn (İntihar Yanması) Kılavuzlama

Gerçek Mars/Ay iniş araçlarının kullandığı "suicide burn" (intihar
yanması) tekniğiyle kontrollü bir Mars inişini simüle eder: araç
olabildiğince geç frenlemeye başlar, tam yere değeceği anda hızını
(neredeyse) sıfıra indirmeye çalışır.
"""

import matplotlib.pyplot as plt

# ----------------------------------------------------------------------
# Fiziksel / kontrol sabitleri
# ----------------------------------------------------------------------
MARS_YERCEKIMI = 3.71        # Mars yerçekimi ivmesi (m/s^2)
MAKS_MOTOR_IVMESI = 7.4      # Motorun maksimum frenleme ivmesi (m/s^2)
ZAMAN_ADIMI = 0.01           # Simülasyon zaman adımı (s)
UST_ESIK = -0.1              # Histerezis üst eşiği (motoru kapat)
ALT_ESIK = -0.3              # Histerezis alt eşiği (motoru aç)
MIN_YANMA_SURESI = 0.5       # Minimum motor açık/kapalı kalma süresi (s)
GUVENLIK_MARJI = 1.05        # Ateşleme güvenlik marjı
YAKIT_TUKETIM_HIZI = 1.5     # Yakıt tüketim hızı (kg/s)
MAKS_SIMULASYON_SURESI = 100.0  # Simülasyon güvenlik zaman sınırı (s)


def inis_simulasyonu(baslangic_yuksekligi, baslangic_hizi, baslangic_yakiti):
    """
    Verilen başlangıç koşulları için tam iniş simülasyonunu çalıştırır.

    Parametreler:
        baslangic_yuksekligi : başlangıç yüksekliği (m)
        baslangic_hizi        : başlangıç hızı (m/s, negatif = aşağı yönde)
        baslangic_yakiti      : başlangıç yakıt miktarı (kg)

    Döndürür:
        zaman/yükseklik/hız/motor/yakıt geçmişi ve özet içeren bir sözlük
    """
    yukseklik = baslangic_yuksekligi
    hiz = baslangic_hizi
    yakit = baslangic_yakiti

    motor_ates_lendi = False
    motor_calisiyor = False
    son_degisim_zamani = -999.0

    zaman_l, yukseklik_l, hiz_l, motor_l, yakit_l = [], [], [], [], []

    t = 0.0
    while yukseklik > 0 and t < MAKS_SIMULASYON_SURESI:
        zaman_l.append(t)
        yukseklik_l.append(yukseklik)
        hiz_l.append(hiz)
        motor_l.append(1 if motor_calisiyor else 0)
        yakit_l.append(yakit)

        # Ateşleme kararı: motoru en son güvenli anda ateşle, net
        # yavaşlama kapasitesine ve güvenlik marjına göre hesaplanır.
        duracak_mesafe = GUVENLIK_MARJI * hiz**2 / (2 * (MAKS_MOTOR_IVMESI - MARS_YERCEKIMI))
        if not motor_ates_lendi and yukseklik <= duracak_mesafe and yakit > 0:
            motor_ates_lendi = True
            motor_calisiyor = True
            son_degisim_zamani = t

        # Minimum açık/kapalı süreli histerezis kontrolü: motor, gerçek
        # bir valfin/motorun yapabileceğinden daha hızlı anahtarlanamaz.
        if motor_ates_lendi:
            zaman_gecti = t - son_degisim_zamani
            if motor_calisiyor and hiz > UST_ESIK and zaman_gecti >= MIN_YANMA_SURESI:
                motor_calisiyor = False
                son_degisim_zamani = t
            elif (not motor_calisiyor) and hiz < ALT_ESIK and zaman_gecti >= MIN_YANMA_SURESI and yakit > 0:
                motor_calisiyor = True
                son_degisim_zamani = t

        # Motor açıkken yakıt tüketimi; yakıt biterse motoru zorla kapat.
        if motor_calisiyor:
            yakit -= YAKIT_TUKETIM_HIZI * ZAMAN_ADIMI
            if yakit <= 0:
                yakit = 0
                motor_calisiyor = False

        # Fizik güncellemesi (yarı-örtük Euler integrasyonu).
        ivme = (-MARS_YERCEKIMI + MAKS_MOTOR_IVMESI) if motor_calisiyor else -MARS_YERCEKIMI
        hiz = hiz + ivme * ZAMAN_ADIMI
        yukseklik = yukseklik + hiz * ZAMAN_ADIMI
        t = t + ZAMAN_ADIMI

    return {
        "zaman": zaman_l, "yukseklik": yukseklik_l, "hiz": hiz_l,
        "motor": motor_l, "yakit": yakit_l,
        "yere_degme_hizi": hiz, "inis_suresi": t, "kalan_yakit": yakit,
    }


# ----------------------------------------------------------------------
# 1) Referans senaryo + 4 panelli tam grafik
# ----------------------------------------------------------------------
referans = inis_simulasyonu(baslangic_yuksekligi=500.0, baslangic_hizi=-20.0, baslangic_yakiti=40.0)
print(f"[Referans] Değme hızı: {referans['yere_degme_hizi']:.2f} m/s | "
      f"Süre: {referans['inis_suresi']:.2f} s | Kalan yakıt: {referans['kalan_yakit']:.2f} kg")

fig, axs = plt.subplots(1, 4, figsize=(18, 4))
axs[0].plot(referans["zaman"], referans["yukseklik"])
axs[0].set_title("Yükseklik - Zaman")
axs[0].set_xlabel("Zaman (s)"); axs[0].set_ylabel("Yükseklik (m)"); axs[0].grid(True)

axs[1].plot(referans["zaman"], referans["hiz"], color="red")
axs[1].set_title("Hız - Zaman")
axs[1].set_xlabel("Zaman (s)"); axs[1].set_ylabel("Hız (m/s)"); axs[1].grid(True)

axs[2].plot(referans["zaman"], referans["motor"], color="green")
axs[2].set_title("Motor Durumu")
axs[2].set_xlabel("Zaman (s)"); axs[2].set_ylabel("0=kapalı, 1=açık"); axs[2].grid(True)

axs[3].plot(referans["zaman"], referans["yakit"], color="orange")
axs[3].set_title("Yakıt - Zaman")
axs[3].set_xlabel("Zaman (s)"); axs[3].set_ylabel("Yakıt (kg)"); axs[3].grid(True)

plt.tight_layout()
plt.show()

# ----------------------------------------------------------------------
# 2) Yakıt stres testi + eşik grafiği
# ----------------------------------------------------------------------
yakit_degerleri = [5, 10, 15, 20, 25, 26, 27, 28, 29, 30, 35, 40, 45]
degme_hizlari = []
for yk in yakit_degerleri:
    s = inis_simulasyonu(baslangic_yuksekligi=500.0, baslangic_hizi=-20.0, baslangic_yakiti=yk)
    degme_hizlari.append(s["yere_degme_hizi"])
    print(f"Yakıt={yk} kg -> Değme hızı={s['yere_degme_hizi']:.2f} m/s, Kalan yakıt={s['kalan_yakit']:.2f} kg")

plt.figure(figsize=(8, 5))
plt.plot(yakit_degerleri, degme_hizlari, marker="o", color="purple")
plt.axhline(y=-1.48, color="green", linestyle="--", label="Güvenli iniş hızı (~-1.48 m/s)")
plt.axvline(x=28, color="red", linestyle="--", label="Kritik yakıt eşiği (~28 kg)")
plt.xlabel("Başlangıç Yakıtı (kg)"); plt.ylabel("Yere Değme Hızı (m/s)")
plt.title("Yakıt Miktarının İniş Güvenliğine Etkisi")
plt.legend(); plt.grid(True); plt.tight_layout()
plt.show()

# ----------------------------------------------------------------------
# 3) Senaryo stres testi + özet çubuk grafik
# ----------------------------------------------------------------------
senaryolar = [
    {"yukseklik": 300.0, "hiz": -10.0, "etiket": "Düşük irtifa\nyavaş"},
    {"yukseklik": 300.0, "hiz": -30.0, "etiket": "Düşük irtifa\nhızlı"},
    {"yukseklik": 500.0, "hiz": -20.0, "etiket": "Orta irtifa\nreferans"},
    {"yukseklik": 800.0, "hiz": -20.0, "etiket": "Yüksek irtifa\norta hız"},
    {"yukseklik": 800.0, "hiz": -40.0, "etiket": "Yüksek irtifa\nhızlı"},
    {"yukseklik": 1000.0, "hiz": -50.0, "etiket": "Çok yüksek\nçok hızlı"},
]

etiketler, senaryo_hizlari = [], []
for s in senaryolar:
    sonuc = inis_simulasyonu(baslangic_yuksekligi=s["yukseklik"], baslangic_hizi=s["hiz"], baslangic_yakiti=50.0)
    etiketler.append(s["etiket"])
    senaryo_hizlari.append(sonuc["yere_degme_hizi"])
    print(f"{s['etiket'].replace(chr(10), ' '):28s} -> Değme hızı={sonuc['yere_degme_hizi']:.2f} m/s, "
          f"Kalan yakıt={sonuc['kalan_yakit']:.2f} kg")

renkler = ["green" if abs(v) < 2.0 else "red" for v in senaryo_hizlari]
plt.figure(figsize=(9, 5))
plt.bar(etiketler, senaryo_hizlari, color=renkler)
plt.axhline(y=-2.0, color="gray", linestyle="--", label="Yumuşak iniş sınırı (~-2 m/s)")
plt.ylabel("Yere Değme Hızı (m/s)")
plt.title("Farklı Senaryolarda İniş Performansı")
plt.legend(); plt.grid(True, axis="y"); plt.tight_layout()
plt.show()
