# sfe.py

import time
import threading
import queue
import os
import cv2
import numpy as np
import mss
# import pytesseract  # KALDIRILDI - Artık Tesseract kullanmıyoruz
import easyocr      # YENİ - EasyOCR kütüphanesini import ediyoruz
import deepl
import keyboard
import pystray
from PIL import Image
from difflib import SequenceMatcher
# Kendi modüllerimizi import edelim
from config_manager import AYARLAR, get_lang, get_resource_path, arayuz_dilini_yukle
from gui import GuiManager

# --- UYGULAMA GENELİ DEĞİŞKENLER ---
gui_queue = queue.Queue()
is_paused = False
son_metin = ""
tray_icon = None
translator = None

# --- KONTROL VE KISAYOL FONKSİYONLARI ---
# Bu bölüm tamamen aynı kalıyor, değişiklik yok.
def register_hotkeys():
    """Ayarlardaki kısayolları sisteme kaydeder."""
    keyboard.unhook_all()
    keyboard.add_hotkey(AYARLAR['durdur_devam_et'], toggle_pause)
    keyboard.add_hotkey(AYARLAR['programi_kapat'], quit_program)
    keyboard.add_hotkey(AYARLAR['alan_sec'], alani_sec_ve_kaydet)

def toggle_pause(*args):
    """Çeviri işlemini durdurur veya devam ettirir."""
    global is_paused, son_metin
    is_paused = not is_paused
    gui_queue.put({'type': 'update_text', 'text': None})
    if is_paused:
        son_metin = ""
    update_tray_menu()

def quit_program(*args):
    """Uygulamayı güvenli bir şekilde kapatır."""
    if tray_icon:
        tray_icon.stop()
    gui_queue.put({'type': 'quit'})

def alani_sec_ve_kaydet():
    """Kullanıcının ekran alanı seçmesini sağlar."""
    was_paused = is_paused
    if not was_paused:
        toggle_pause()
    gui_queue.put({'type': 'open_selector'})

def ayarlari_penceresini_ac():
    """Ayarlar penceresini açmak için GUI'ye mesaj gönderir."""
    gui_queue.put({'type': 'open_settings'})

def update_tray_menu():
    """Sistem tepsisi menüsünü güncel durum ve dile göre yeniler."""
    global tray_icon
    if not tray_icon:
        return
        
    pause_text = get_lang('menu_resume') if is_paused else get_lang('menu_pause')
    new_menu = pystray.Menu(
        pystray.MenuItem(pause_text, toggle_pause),
        pystray.MenuItem(get_lang('menu_select_area'), alani_sec_ve_kaydet),
        pystray.MenuItem(get_lang('menu_settings'), ayarlari_penceresini_ac),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(get_lang('menu_exit'), quit_program)
    )
    tray_icon.title = get_lang('app_title')
    tray_icon.menu = new_menu

# --- ANA ÇEVİRİ DÖNGÜSÜ (EASYOCR İLE GÜNCELLENDİ) ---
def main_translation_loop():
    """Ekranı tarayan, OCR yapan ve çeviriyi tetikleyen ana döngü."""
    global son_metin, translator
    
    # DeepL translator'ı başlat
    try:
        translator = deepl.Translator(AYARLAR['api_anahtari'])
    except Exception as e:
        print(f"HATA: DeepL Translator oluşturulamadı: {e}.")
        gui_queue.put({
            'type': 'show_message_error',
            'title': get_lang('error_title_deepl'),
            'body': get_lang('error_body_deepl_key')
        })
        translator = None

    # YENİ: EasyOCR okuyucusunu başlat.
    # Bu işlem model dosyalarını belleğe yüklediği için birkaç saniye sürebilir.
    # Sadece bir kere, döngünün dışında yapıyoruz.
    # GPU kullanmak için: easyocr.Reader(['en'], gpu=True)
    print("EasyOCR modeli yükleniyor... Bu işlem biraz zaman alabilir.")
    try:
        reader = easyocr.Reader(['en'], gpu=False) 
        print("EasyOCR modeli başarıyla yüklendi.")
    except Exception as e:
        print(f"HATA: EasyOCR başlatılamadı: {e}")
        gui_queue.put({
            'type': 'show_message_error',
            'title': "EasyOCR Hatası",
            'body': f"EasyOCR başlatılamadı. Kütüphanenin doğru kurulduğundan emin olun.\n\nHata: {e}"
        })
        return # Fonksiyondan çık, thread dursun.

    sct = mss.mss()
    while True:
        try:
            if not is_paused:
                bolge = {
                    'top': AYARLAR['top'], 'left': AYARLAR['left'],
                    'width': AYARLAR['width'], 'height': AYARLAR['height']
                }

                ekran_goruntusu = sct.grab(bolge)
                img = np.array(ekran_goruntusu)
                
                # DEĞİŞTİ: EasyOCR ile metin okuma
                # EasyOCR renkli görüntü ile daha iyi çalışır, bu yüzden
                # griye çevirme veya threshold gibi ön işlemlere gerek yoktur.
                results = reader.readtext(img)
                
                # EasyOCR'ın bulduğu tüm metin parçalarını birleştiriyoruz.
                # `results` formatı: [(bounding_box, 'metin', güven_skoru), ...]
                temiz_metin = ' '.join([res[1] for res in results]).strip()
                
                similarity_ratio = SequenceMatcher(None, temiz_metin, son_metin).ratio()
                
                if temiz_metin and similarity_ratio < AYARLAR['benzerlik_orani_esigi']:
                    son_metin = temiz_metin
                    if translator:
                        try:
                            if not is_paused:
                                cevirilmis = translator.translate_text(temiz_metin, target_lang=AYARLAR['hedef_dil'])
                                if not is_paused:
                                    gui_queue.put({'type': 'update_text', 'text': cevirilmis.text})
                        except Exception as e:
                            print(f"Çeviri hatası: {e}")
                            if not is_paused:
                                gui_queue.put({'type': 'update_text', 'text': f"[{get_lang('error_translation')}]"})
                elif not temiz_metin and son_metin:
                    son_metin = ""
                    gui_queue.put({'type': 'update_text', 'text': ""})
            
            time.sleep(AYARLAR.get('kontrol_araligi', 0.5))

        except Exception as e:
            print(f"Ana döngüde beklenmedik hata: {e}")
            time.sleep(2)

# --- ANA PROGRAM BAŞLANGIÇ NOKTASI ---
# Bu bölüm tamamen aynı kalıyor, değişiklik yok.
if __name__ == "__main__":
    # Tesseract yolunu ayarlama satırını siliyoruz.
    # pytesseract.pytesseract.tesseract_cmd = AYARLAR['tesseract_yolu'] # KALDIRILDI

    if not AYARLAR['baslangicta_baslat'] or AYARLAR['width'] < 10 or AYARLAR['height'] < 10:
        is_paused = True
    
    hotkey_callbacks = {
        'register': register_hotkeys,
        'update_tray': update_tray_menu
    }

    gui_manager_thread = threading.Thread(target=lambda: GuiManager(gui_queue, hotkey_callbacks))
    gui_manager_thread.start()
    
    translation_thread = threading.Thread(target=main_translation_loop, daemon=True)
    translation_thread.start()
    
    register_hotkeys()
    
    image = Image.open(get_resource_path("icon.png"))
    tray_icon = pystray.Icon(get_lang("app_title"), image, menu=pystray.Menu())
    
    update_tray_menu()
    
    tray_icon.run()

    os._exit(0)