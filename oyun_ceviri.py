import time
import cv2
import numpy as np
import mss
import pytesseract
import deepl
import tkinter as tk
import threading
import keyboard
import os
import configparser # YENİ: Ayar dosyasını okumak için

# ------------------- AYARLARI config.ini DOSYASINDAN OKUMA -------------------
# YENİ: Tüm ayarlar bölümü artık bu bloktan yönetiliyor.

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8') # UTF-8 desteği ekledik

# Genel Ayarlar
TESSERACT_YOLU = config.get('Genel', 'tesseract_yolu')
DEEPL_API_KEY = config.get('Genel', 'api_anahtari')

# Bölge Ayarları
altyazi_bolgesi = {
    'top': config.getint('Bolge', 'top'),
    'left': config.getint('Bolge', 'left'),
    'width': config.getint('Bolge', 'width'),
    'height': config.getint('Bolge', 'height')
}

# Arayüz Ayarları
FONT_BOYUTU = config.getint('Arayuz', 'font_boyutu')
FONT_RENGI = config.get('Arayuz', 'font_rengi')
ARKA_PLAN_RENGI = config.get('Arayuz', 'arka_plan_rengi')
SEFFAFLIK = config.getfloat('Arayuz', 'seffaflik')
EKRAN_UST_BOSLUK = config.getint('Arayuz', 'ekran_ust_bosluk')
KONTROL_ARALIGI = config.getfloat('Arayuz', 'kontrol_araligi')

# Kısayol Ayarları
DURDUR_DEVAM_ET_TUSU = config.get('Kisayollar', 'durdur_devam_et')
PROGRAMI_KAPAT_TUSU = config.get('Kisayollar', 'programi_kapat')

# Tesseract yolunu ayarla
pytesseract.pytesseract.tesseract_cmd = TESSERACT_YOLU

# ------------------------------------------------------------------------------------

# Global Değişkenler ve Fonksiyonlar (Önceki kodla neredeyse aynı)
son_metin = ""
is_paused = False
translator = deepl.Translator(DEEPL_API_KEY)
sct = mss.mss()
gui = None

def toggle_pause():
    global is_paused
    is_paused = not is_paused
    status = "DURAKLATILDI" if is_paused else "DEVAM EDİYOR"
    print(f"\n--- ÇEVİRİ {status} --- (Kısayol: {DURDUR_DEVAM_ET_TUSU})")
    if is_paused and gui:
        gui.update_text("")

def quit_program():
    print(f"\n--- '{PROGRAMI_KAPAT_TUSU}' basıldı. Program kapatılıyor... ---")
    if gui:
        gui.root.quit()
    os._exit(0)

# OverlayGUI sınıfı ve diğer fonksiyonlar (Değişiklik yok)
class OverlayGUI:
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
    
# main_translation_loop fonksiyonu (Değişiklik yok)
def main_translation_loop():
    global son_metin, is_paused
    time.sleep(2)
    while True:
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
        time.sleep(KONTROL_ARALIGI)

if __name__ == "__main__":
    # Klavye kısayollarını config dosyasından okunan değerlerle ayarla
    keyboard.add_hotkey(DURDUR_DEVAM_ET_TUSU, toggle_pause)
    keyboard.add_hotkey(PROGRAMI_KAPAT_TUSU, quit_program)

    print("Ayarlar 'config.ini' dosyasından yüklendi.")
    print("Program başlatıldı. Arayüz yükleniyor...")
    print("--------------------------------------------------")
    print("KONTROLLER:")
    print(f"{DURDUR_DEVAM_ET_TUSU} -> Çeviriyi Duraklat / Devam Ettir")
    print(f"{PROGRAMI_KAPAT_TUSU} -> Programı Kapat")
    print("--------------------------------------------------")

    gui_thread = threading.Thread(target=start_gui, daemon=True)
    gui_thread.start()

    main_translation_loop()