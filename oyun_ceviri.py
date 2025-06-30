import time
import cv2
import numpy as np
import mss
import pytesseract
import deepl
import tkinter as tk
import threading
import keyboard  # YENİ: Klavye dinleme kütüphanesi
import os        # YENİ: Programı kapatmak için

# ------------------- AYARLAR BÖLÜMÜ (BURAYI KENDİNE GÖRE DÜZENLE) -------------------

# 1. Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 2. Altyazı Bölgesi
altyazi_bolgesi = {'top': 966, 'left': 599, 'width': 726, 'height': 112}

# 3. DeepL API Anahtarı
DEEPL_API_KEY = "1586ca4b-6a12-479d-96be-49de1f5b190d:fx"

# 4. Arayüz Ayarları
FONT_BOYUTU = 20
FONT_RENGI = "white"
ARKA_PLAN_RENGI = "black"
SEFFAFLIK = 0.7
EKRAN_UST_BOSLUK = 30
KONTROL_ARALIGI = 0.5

# ------------------------------------------------------------------------------------

# Global Değişkenler
son_metin = ""
is_paused = False  # YENİ: Duraklatma durumunu tutan bayrak
translator = deepl.Translator(DEEPL_API_KEY)
sct = mss.mss()
gui = None

# YENİ: Programı Duraklatma/Devam ettirme fonksiyonu
def toggle_pause():
    global is_paused
    is_paused = not is_paused  # Durumu tersine çevir (True ise False, False ise True)
    status = "DURAKLATILDI" if is_paused else "DEVAM EDİYOR"
    print(f"\n--- ÇEVİRİ {status} --- (Devam etmek/duraklatmak için F9)")
    
    # Duraklatıldığında ekrandaki yazıyı temizle
    if is_paused and gui:
        gui.update_text("")

# YENİ: Programı güvenli bir şekilde kapatma fonksiyonu
def quit_program():
    print("\n--- F10'a basıldı. Program kapatılıyor... ---")
    gui.root.quit() # Önce GUI'yi kapat
    os._exit(0)     # Sonra tüm programı sonlandır

# Arayüzü oluşturacak ve yönetecek sınıf (Değişiklik yok)
class OverlayGUI:
    # ... Bu sınıfın içeriği önceki kodla aynı, o yüzden buraya tekrar kopyalamıyorum ...
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-alpha", SEFFAFLIK)
        self.root.config(bg=ARKA_PLAN_RENGI)
        self.screen_width = self.root.winfo_screenwidth()
        self.label = tk.Label(self.root, text="", font=("Arial", FONT_BOYUTU, "bold"), fg=FONT_RENGI, bg=ARKA_PLAN_RENGI, wraplength=self.screen_width * 0.8, justify="center", padx=15, pady=10)
        self.label.pack()
    def update_text(self, text):
        if not text:
            self.root.geometry('1x1+-10+-10')
            return
        self.label.config(text=text)
        self.root.update_idletasks()
        width = self.label.winfo_reqwidth()
        height = self.label.winfo_reqheight()
        x = (self.screen_width // 2) - (width // 2)
        y = EKRAN_UST_BOSLUK
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    def run(self):
        self.root.mainloop()

def start_gui():
    global gui
    gui = OverlayGUI()
    gui.run()

# Ana çeviri döngüsü
def main_translation_loop():
    global son_metin, is_paused

    time.sleep(2)

    while True:
        # DEĞİŞTİRİLDİ: Ana döngünün başına duraklatma kontrolü eklendi
        if not is_paused:
            try:
                ekran_goruntusu = sct.grab(altyazi_bolgesi)
                img = np.array(ekran_goruntusu)
                gri_img = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
                _, islenmis_img = cv2.threshold(gri_img, 180, 255, cv2.THRESH_BINARY_INV)
                metin = pytesseract.image_to_string(islenmis_img, lang='eng')
                temiz_metin = metin.strip().replace('\n', ' ')

                if temiz_metin and temiz_metin != son_metin:
                    son_metin = temiz_metin
                    print(f"Orijinal: {temiz_metin}")
                    try:
                        cevirilmis = translator.translate_text(temiz_metin, source_lang="EN", target_lang="TR")
                        if gui:
                            gui.update_text(cevirilmis.text)
                    except Exception as e:
                        print(f"!! ÇEVİRİ HATASI: {e}")
                        if gui:
                            gui.update_text("[Çeviri alınamadı...]")
                elif not temiz_metin and son_metin:
                    son_metin = ""
                    if gui:
                        gui.update_text("")
            except Exception as e:
                print(f"KRİTİK HATA: {e}")
                son_metin = ""
                if gui:
                    gui.update_text("[Program hatası...]")
        
        # Bekleme komutu döngünün sonuna taşındı ki her durumda çalışsın
        time.sleep(KONTROL_ARALIGI)

if __name__ == "__main__":
    # YENİ: Klavye kısayollarını ayarla
    keyboard.add_hotkey('f9', toggle_pause)
    keyboard.add_hotkey('f10', quit_program)

    print("Program başlatıldı. Arayüz yükleniyor...")
    print("--------------------------------------------------")
    print("KONTROLLER:")
    print("F9 -> Çeviriyi Duraklat / Devam Ettir")
    print("F10 -> Programı Kapat")
    print("--------------------------------------------------")

    gui_thread = threading.Thread(target=start_gui, daemon=True)
    gui_thread.start()

    main_translation_loop()