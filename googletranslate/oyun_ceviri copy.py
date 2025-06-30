import time
import cv2  # OpenCV kütüphanesi
import numpy as np
import mss
import pytesseract
from googletrans import Translator

# ------------------- AYARLAR BÖLÜMÜ (BURAYI KENDİNE GÖRE DÜZENLE) -------------------

# 1. Tesseract'ı kurduğun yolu buraya yaz.
# Genellikle 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe' olur.
# Başındaki 'r' harfini ve tırnak işaretlerini silme.
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 2. Altyazıların ekranda göründüğü alanı belirle.
# 'top' = Ekranın üstünden altyazı alanının başlangıcına olan piksel mesafesi
# 'left' = Ekranın solundan altyazı alanının başlangıcına olan piksel mesafesi
# 'width' = Altyazı alanının genişliği
# 'height' = Altyazı alanının yüksekliği
# BU DEĞERLERİ BİR SONRAKİ ADIMDA NASIL BULACAĞINI ANLATACAĞIM.
altyazi_bolgesi = {'top': 966, 'left': 599, 'width': 726, 'height': 112}
# 3. Çeviri Ayarları
kaynak_dil = 'en'  # Altyazının orijinal dili (İngilizce için 'en')
hedef_dil = 'tr'   # Çevrilecek dil (Türkçe için 'tr')

# ------------------------------------------------------------------------------------


# Çevirmen ve ekran yakalama araçlarını başlat
translator = Translator()
sct = mss.mss()

son_metin = ""

print("Program başlatıldı. Çeviri için bekleniyor...")
print("Programı durdurmak için komut ekranına tıklayıp CTRL+C tuşlarına basın.")

while True:
    try:
        # Belirtilen bölgenin ekran görüntüsünü al
        ekran_goruntusu = sct.grab(altyazi_bolgesi)
        
        # Görüntüyü OpenCV'nin anlayacağı formata çevir
        img = np.array(ekran_goruntusu)
        
        # --- GÖRÜNTÜ ÖN İŞLEME (OCR DOĞRULUĞUNU ARTIRMAK İÇİN) ---
        # Görüntüyü gri tonlamalı yap
        gri_img = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
        
        # Eşikleme (thresholding) uygulayarak yazıyı netleştir.
        # Bu işlem, görüntüyü sadece siyah ve beyaz piksellere dönüştürür.
        # 180 değeri ışığa/oyuna göre ayarlanabilir. Genellikle 150-200 arası iyi çalışır.
        _, islenmis_img = cv2.threshold(gri_img, 180, 255, cv2.THRESH_BINARY)
        
        # Görüntüdeki metni Tesseract ile oku
        # lang='eng' İngilizce metin okuyacağını belirtir
        metin = pytesseract.image_to_string(islenmis_img, lang='eng')
        
        # Okunan metindeki satır sonu gibi gereksiz karakterleri temizle
        temiz_metin = metin.strip().replace('\n', ' ')
        
        # Eğer yeni bir metin okunduysa ve bu metin bir öncekiyle aynı değilse
        if temiz_metin and temiz_metin != son_metin:
            son_metin = temiz_metin
            
            print("\n----------------------------------")
            print(f"Orijinal Metin: {temiz_metin}")
            
            # Metni çevir
            cevirilmis = translator.translate(temiz_metin, src=kaynak_dil, dest=hedef_dil)
            
            print(f"Çeviri: {cevirilmis.text}")
            
        # Programın çok hızlı çalışıp sistemi yormaması için kısa bir bekleme
        time.sleep(1)

    except Exception as e:
        # Bir hata olursa programın çökmesini engelle ve hatayı yazdır
        print(f"Bir hata oluştu: {e}")
        son_metin = "" # Hata sonrası metin belleğini sıfırla
        time.sleep(2)