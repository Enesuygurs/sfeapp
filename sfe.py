# sfe.py (Tesseract ile çalışan tam kod)

import time
import threading
import queue
import os
import cv2
import numpy as np
import mss
import pytesseract # Tesseract'e geri döndük
import deepl
import keyboard
import pystray
from PIL import Image
from difflib import SequenceMatcher
from config_manager import AYARLAR, get_lang, get_resource_path, arayuz_dilini_yukle
from gui import GuiManager

# --- DEĞİŞKENLER (DEĞİŞİKLİK YOK) ---
gui_queue = queue.Queue()
is_paused = False
son_metin = ""
tray_icon = None
translator = None

# --- KISAYOL FONKSİYONLARI (DEĞİŞİKLİK YOK) ---
def register_hotkeys():
    keyboard.unhook_all()
    keyboard.add_hotkey(AYARLAR['durdur_devam_et'], toggle_pause)
    keyboard.add_hotkey(AYARLAR['programi_kapat'], quit_program)
    keyboard.add_hotkey(AYARLAR['alan_sec'], alani_sec_ve_kaydet)

def toggle_pause(*args):
    global is_paused, son_metin
    is_paused = not is_paused
    gui_queue.put({'type': 'update_text', 'text': None})
    if is_paused: son_metin = ""
    update_tray_menu()

def quit_program(*args):
    if tray_icon: tray_icon.stop()
    gui_queue.put({'type': 'quit'})

def alani_sec_ve_kaydet():
    was_paused = is_paused
    if not was_paused: toggle_pause()
    gui_queue.put({'type': 'open_selector'})

def ayarlari_penceresini_ac():
    gui_queue.put({'type': 'open_settings'})

def update_tray_menu():
    global tray_icon
    if not tray_icon: return
    pause_text = get_lang('menu_resume') if is_paused else get_lang('menu_pause')
    new_menu = pystray.Menu(pystray.MenuItem(pause_text, toggle_pause), pystray.MenuItem(get_lang('menu_select_area'), alani_sec_ve_kaydet), pystray.MenuItem(get_lang('menu_settings'), ayarlari_penceresini_ac), pystray.Menu.SEPARATOR, pystray.MenuItem(get_lang('menu_exit'), quit_program))
    tray_icon.title = get_lang('app_title')
    tray_icon.menu = new_menu

# --- ANA ÇEVİRİ DÖNGÜSÜ (TESSERACT İÇİN OPTİMİZE EDİLDİ) ---
def main_translation_loop():
    global son_metin, translator

    try:
        translator = deepl.Translator(AYARLAR['api_anahtari'])
    except Exception as e:
        print(f"HATA: DeepL Translator oluşturulamadı: {e}.")
        gui_queue.put({'type': 'show_message_error', 'title': get_lang('error_title_deepl'), 'body': get_lang('error_body_deepl_key')})
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

                bolge = {'top': AYARLAR['top'], 'left': AYARLAR['left'], 'width': AYARLAR['width'], 'height': AYARLAR['height']}
                ekran_goruntusu = sct.grab(bolge)
                img = np.array(ekran_goruntusu)
                
                # --- GÖRÜNTÜ İŞLEME ---
                islenmis_img = None
                if AYARLAR['isleme_modu'] == 'renk':
                    # Renk tabanlı maskeleme (Yüksek doğruluk)

                    # 1. Adım: BGRA'dan BGR'ye çevir (Alfa kanalını kaldır)
                    bgr_img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                    
                    # 2. Adım: BGR'den HSV'ye çevir
                    hsv_img = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2HSV)

                    lower_bound = np.array([AYARLAR['renk_alt_sinir_h'], AYARLAR['renk_alt_sinir_s'], AYARLAR['renk_alt_sinir_v']])
                    upper_bound = np.array([AYARLAR['renk_ust_sinir_h'], AYARLAR['renk_ust_sinir_s'], AYARLAR['renk_ust_sinir_v']])
                    mask = cv2.inRange(hsv_img, lower_bound, upper_bound)
                    islenmis_img = cv2.bitwise_not(mask) # Tesseract siyah metin-beyaz arkaplan sever
                else: # 'esik' modu
                    # Basit eşikleme (Daha hızlı ama daha az güvenilir)
                    gri_img = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
                    _, islenmis_img = cv2.threshold(gri_img, AYARLAR['esik_degeri'], 255, cv2.THRESH_BINARY)

                # Tesseract'e metnin tek bir blok olduğunu söyleyelim
                custom_config = r'--oem 3 --psm 6'
                metin = pytesseract.image_to_string(islenmis_img, lang='eng', config=custom_config)
                temiz_metin = metin.strip().replace('\n', ' ')

                similarity_ratio = SequenceMatcher(None, temiz_metin, son_metin).ratio()
                if temiz_metin and similarity_ratio < AYARLAR['benzerlik_orani_esigi']:
                    son_metin = temiz_metin
                    if translator and not is_paused:
                        try:
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
            
            time.sleep(AYARLAR.get('kontrol_araligi', 0.4))

        except Exception as e:
            print(f"Ana döngüde beklenmedik hata: {e}")
            time.sleep(2)

# --- ANA PROGRAM BAŞLANGIÇ NOKTASI ---
if __name__ == "__main__":
    pytesseract.pytesseract.tesseract_cmd = AYARLAR['tesseract_yolu']

    if not AYARLAR['baslangicta_baslat'] or AYARLAR['width'] < 10 or AYARLAR['height'] < 10:
        is_paused = True
    
    hotkey_callbacks = {'register': register_hotkeys, 'update_tray': update_tray_menu}
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