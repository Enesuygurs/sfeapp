import time
import cv2
import numpy as np
import mss
import pytesseract
import deepl
import tkinter as tk
import threading

# ------------------- AYARLAR BÖLÜMÜ (BURAYI KENDİNE GÖRE DÜZENLE) -------------------

# 1. Tesseract'ı kurduğun yolu buraya yaz.
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 2. Altyazıların ekranda göründüğü alan.
altyazi_bolgesi = {'top': 966, 'left': 599, 'width': 726, 'height': 112}

# 3. DeepL API Anahtarı (LÜTFEN BU ANAHTARI GİZLİ TUTUN)
DEEPL_API_KEY = "1586ca4b-6a12-479d-96be-49de1f5b190d:fx" # Lütfen yeni anahtarını kullan

# 4. Arayüz (Overlay) Ayarları
FONT_BOYUTU = 20
FONT_RENGI = "white"
ARKA_PLAN_RENGI = "black"
SEFFAFLIK = 0.7
EKRAN_UST_BOSLUK = 30
KONTROL_ARALIGI = 0.5

# ------------------------------------------------------------------------------------

# Global değişkenler
son_metin = ""
translator = deepl.Translator(DEEPL_API_KEY)
sct = mss.mss()
gui = None

# Arayüzü oluşturacak ve yönetecek sınıf
class OverlayGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-alpha", SEFFAFLIK)
        self.root.config(bg=ARKA_PLAN_RENGI)
        
        self.screen_width = self.root.winfo_screenwidth()
        
        self.label = tk.Label(self.root, text="", 
                              font=("Arial", FONT_BOYUTU, "bold"), 
                              fg=FONT_RENGI, 
                              bg=ARKA_PLAN_RENGI,
                              wraplength=self.screen_width * 0.8, # Genişlik sınırını biraz artırdım
                              justify="center",
                              padx=15, pady=10) # Kenar boşluklarını artırdım
        
        # DİNAMİK BOYUTLANDIRMA İÇİN GÜNCELLENDİ:
        # Etiketi daha basit bir şekilde paketleyerek içeriğe göre boyutlanmasını sağlıyoruz.
        self.label.pack()

    def update_text(self, text):
        if not text:
            # Metin yoksa pencereyi görünmez yap (kapatmak yerine)
            self.root.geometry('1x1+-10+-10') # Ekran dışında 1x1 piksel bir alana taşı
            return

        self.label.config(text=text)
        # Pencerenin boyutunu içeriğe göre otomatik olarak ayarlamasını sağla
        self.root.update_idletasks()
        
        width = self.label.winfo_reqwidth() # Gerekli genişliği al
        height = self.label.winfo_reqheight() # Gerekli yüksekliği al
        x = (self.screen_width // 2) - (width // 2)
        y = EKRAN_UST_BOSLUK
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def run(self):
        self.root.mainloop()

# Arayüzü ayrı bir thread'de başlatacak fonksiyon
def start_gui():
    global gui
    gui = OverlayGUI()
    gui.run()

# Ana çeviri döngüsü
def main_translation_loop():
    global son_metin
    
    time.sleep(2)

    while True:
        try: # Bu dış try-except, ekran görüntüsü alma gibi kritik hatalar için kalmalı
            ekran_goruntusu = sct.grab(altyazi_bolgesi)
            img = np.array(ekran_goruntusu)
            gri_img = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
            _, islenmis_img = cv2.threshold(gri_img, 180, 255, cv2.THRESH_BINARY_INV) # Bazen beyaz yazı için INV daha iyi çalışır
            metin = pytesseract.image_to_string(islenmis_img, lang='eng')
            temiz_metin = metin.strip().replace('\n', ' ')

            if temiz_metin and temiz_metin != son_metin:
                # ÖNEMLİ: Metni önbelleğe alıp orijinalini hemen yazdırıyoruz.
                # Çeviri başarısız olsa bile bir sonraki denemede aynı metni tekrar çevirmeyecek.
                son_metin = temiz_metin
                print(f"Orijinal: {temiz_metin}")

                # HATA YÖNETİMİ İÇİN GÜNCELLENDİ:
                # Sadece çeviri işlemini ayrı bir try-except bloğuna alıyoruz.
                try:
                    cevirilmis = translator.translate_text(temiz_metin, source_lang="EN", target_lang="TR")
                    if gui:
                        gui.update_text(cevirilmis.text)
                except Exception as e:
                    print(f"!! ÇEVİRİ HATASI: {e}")
                    if gui:
                        # Hata durumunda kullanıcıya bilgi ver ama programı kilitleme
                        gui.update_text("[Çeviri alınamadı...]")

            elif not temiz_metin and son_metin:
                son_metin = ""
                if gui:
                    gui.update_text("")

            time.sleep(KONTROL_ARALIGI)

        except Exception as e:
            # Bu blok artık sadece ekran görüntüsü alma gibi daha temel hataları yakalar
            print(f"KRİTİK HATA: {e}")
            son_metin = ""
            if gui:
                gui.update_text("[Program hatası...]")
            time.sleep(2)

if __name__ == "__main__":
    print("Program başlatıldı. Arayüz yükleniyor...")
    print("Programı durdurmak için bu pencereye tıklayıp CTRL+C tuşlarına basın.")

    gui_thread = threading.Thread(target=start_gui, daemon=True)
    gui_thread.start()

    main_translation_loop()