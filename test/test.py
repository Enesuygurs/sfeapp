# tespit_araci.py

import cv2
import numpy as np

# Bu fonksiyon penceredeki kaydırıcı her hareket ettiğinde çalışacak
def on_trackbar_change(val):
    # Kaydırıcıdan mevcut eşik değerini oku
    threshold_value = val
    
    # Görüntüyü yeniden işle
    # 1. Gri tona çevir
    gray_img = cv2.cvtColor(original_img, cv2.COLOR_BGR2GRAY)
    
    # 2. Kaydırıcıdan gelen DEĞİŞKEN değerle eşikleme yap
    # Bu, açık renkli yazıları siyaha, koyu zemini beyaza çevirir
    _, processed_img = cv2.threshold(gray_img, threshold_value, 255, cv2.THRESH_BINARY_INV)
    
    # İşlenmiş görüntüyü pencerede göster
    cv2.imshow("İşlenmiş Görüntü", processed_img)

# --- ANA KOD ---
try:
    # 1. Adım'da kaydettiğiniz test görüntüsünü yükle
    original_img = cv2.imread('test_goruntusu.png')
    if original_img is None:
        print("HATA: 'test_goruntusu.png' bulunamadı!")
        print("Lütfen altyazı bölgesinin ekran görüntüsünü alıp bu isimle kaydedin.")
        exit()
except Exception as e:
    print(f"Görüntü yüklenirken hata oluştu: {e}")
    exit()


# Kontrol penceresini ve kaydırıcıyı oluştur
window_name = "Eşik Değeri Ayarlayıcı"
cv2.namedWindow(window_name)
# 0 ile 255 arasında değişen bir kaydırıcı oluştur. Başlangıç değeri 127 olsun.
cv2.createTrackbar("Threshold Değeri", window_name, 127, 255, on_trackbar_change)

# Orijinal ve işlenmiş görüntü pencerelerini oluştur
cv2.imshow("Orijinal Görüntü", original_img)
cv2.imshow("İşlenmiş Görüntü", np.zeros_like(original_img[:,:,0])) # Başlangıçta boş göster

# İlk görüntüyü oluşturmak için fonksiyonu bir kez çağır
on_trackbar_change(127)

print("Pencereleri kapatmak için 'q' tuşuna basın.")
# 'q' tuşuna basılana kadar pencereleri açık tut
while True:
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()