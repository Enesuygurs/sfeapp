# sfe.py

import time
import threading
import queue
import os
import cv2
import numpy as np
import mss
import pytesseract
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
icon_running = None
icon_stopped = None

# --- KONTROL VE KISAYOL FONKSİYONLARI ---
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
    gui_queue.put({'type': 'update_text', 'text': None}) # Overlay'i gizle
    if is_paused:
        son_metin = ""
    update_tray_menu()

def quit_program(*args):
    """Uygulamayı güvenli bir şekilde kapatır."""
    if tray_icon:
        tray_icon.stop()
    gui_queue.put({'type': 'quit'})

# DEĞİŞTİRİLDİ: Bu fonksiyon artık işlem sonrası devam etme mantığını içeriyor
def alani_sec_ve_kaydet():
    """Kullanıcının ekran alanı seçmesini sağlar ve gerekirse çeviriyi devam ettirir."""
    # Çevirinin alan seçilmeden önce çalışıp çalışmadığını kontrol et.
    # Eğer çalışıyorsa (yani 'is_paused' False ise), işlem bitince devam etmeliyiz.
    should_resume_after = not is_paused
    
    # Eğer çalışıyorsa, alan seçimi için geçici olarak duraklat
    if should_resume_after:
        toggle_pause() 
    
    # GUI'ye hem seçiciyi açmasını söyle, hem de işlem bitince devam edilip
    # edilmeyeceği bilgisini gönder.
    gui_queue.put({'type': 'open_selector', 'should_resume': should_resume_after})

def ayarlari_penceresini_ac():
    """Ayarlar penceresini açmak için GUI'ye mesaj gönderir."""
    gui_queue.put({'type': 'open_settings'})

def update_tray_menu():
    """Sistem tepsisi menüsünü ve İKONUNU güncel durum ve dile göre yeniler."""
    global tray_icon
    if not tray_icon:
        return

    if icon_stopped and icon_running:
        tray_icon.icon = icon_stopped if is_paused else icon_running
        
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

# --- ANA ÇEVİRİ DÖNGÜSÜ ---
def main_translation_loop():
    """Ekranı tarayan, OCR yapan ve çeviriyi tetikleyen ana döngü."""
    global son_metin, translator
    
    try:
        translator = deepl.Translator(AYARLAR['api_anahtari'])
    except Exception as e:
        print(f"HATA: DeepL Translator oluşturulamadı: {e}. API Anahtarı geçersiz olabilir.")
        gui_queue.put({
            'type': 'show_message_error',
            'title': get_lang('error_title_deepl'),
            'body': get_lang('error_body_deepl_key')
        })
        translator = None
    
    sct = mss.mss()
    while True:
        try:
            if not is_paused:
                if not os.path.exists(AYARLAR['tesseract_yolu']):
                    if not is_paused: toggle_pause()
                    gui_queue.put({'type': 'show_message_error', 'title': get_lang('error_tesseract_path_title'), 'body': get_lang('error_tesseract_path_body')})
                    gui_queue.put({'type': 'open_settings'})
                    time.sleep(5)
                    continue

                bolge = {
                    'top': AYARLAR['top'], 'left': AYARLAR['left'],
                    'width': AYARLAR['width'], 'height': AYARLAR['height']
                }
                
                if bolge['width'] < 10 or bolge['height'] < 10:
                    time.sleep(1) # Alan seçilmemişse döngüyü yavaşlat
                    continue

                ekran_goruntusu = sct.grab(bolge)
                img = np.array(ekran_goruntusu)
                gri_img = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
                _, islenmis_img = cv2.threshold(gri_img, 180, 255, cv2.THRESH_BINARY_INV)
                
                metin = pytesseract.image_to_string(islenmis_img, lang='eng')
                temiz_metin = metin.strip().replace('\n', ' ')
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
if __name__ == "__main__":
    pytesseract.pytesseract.tesseract_cmd = AYARLAR['tesseract_yolu']

    if not AYARLAR['baslangicta_baslat'] or AYARLAR['width'] < 10 or AYARLAR['height'] < 10:
        is_paused = True
    
    # DEĞİŞTİRİLDİ: 'toggle' anahtarı ile toggle_pause fonksiyonunu GUI'ye gönderiyoruz.
    hotkey_callbacks = {
        'register': register_hotkeys,
        'update_tray': update_tray_menu,
        'toggle': toggle_pause 
    }

    gui_manager_thread = threading.Thread(target=lambda: GuiManager(gui_queue, hotkey_callbacks))
    gui_manager_thread.start()
    
    translation_thread = threading.Thread(target=main_translation_loop, daemon=True)
    translation_thread.start()
    
    register_hotkeys()
    
    try:
        icon_running = Image.open(get_resource_path("images/icon.png"))
        icon_stopped = Image.open(get_resource_path("images/stop.png"))
    except FileNotFoundError:
        print("HATA: İkon dosyaları (icon.png, stop.png) 'images' klasöründe bulunamadı!")
        try:
             icon_running = Image.open(get_resource_path("images/icon.png"))
        except:
             icon_running = Image.new('RGB', (64, 64), color = 'red') # Fallback
        icon_stopped = icon_running

    initial_icon = icon_stopped if is_paused else icon_running
    
    tray_icon = pystray.Icon(
        get_lang("app_title"), 
        initial_icon,
        menu=pystray.Menu()
    )
    
    update_tray_menu()
    
    tray_icon.run()

    os._exit(0)