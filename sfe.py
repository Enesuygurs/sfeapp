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
import re
from difflib import SequenceMatcher
from config_manager import SETTINGS as AYARLAR, get_lang, get_resource_path, load_interface_language
from gui import GuiManager

gui_queue = queue.Queue()
is_paused = False
last_text = ""
tray_icon = None
translator = None
icon_running = None
icon_stopped = None
ocr_allowed = None

def register_hotkeys():
    keyboard.unhook_all()
    keyboard.add_hotkey(AYARLAR['durdur_devam_et'], toggle_pause)
    keyboard.add_hotkey(AYARLAR['programi_kapat'], quit_program)
    keyboard.add_hotkey(AYARLAR['alan_sec'], select_area_and_save)

def toggle_pause(*args):
    global is_paused
    is_paused = not is_paused
    print(f"\n--- Çeviri {'DURDURULDU' if is_paused else 'BAŞLATILDI'} ---")
    update_tray_menu()

def quit_program(*args):
    if tray_icon: tray_icon.stop()
    gui_queue.put({'type': 'quit'})

def select_area_and_save():
    should_resume_after = not is_paused
    if should_resume_after: toggle_pause()
    gui_queue.put({'type': 'open_selector', 'should_resume': should_resume_after})

def open_settings_window():
    gui_queue.put({'type': 'open_settings'})

def update_tray_menu():
    global tray_icon
    if not tray_icon: return
    if icon_stopped and icon_running:
        tray_icon.icon = icon_stopped if is_paused else icon_running
    pause_text = get_lang('menu_resume') if is_paused else get_lang('menu_pause')
    new_menu = pystray.Menu(
        pystray.MenuItem(pause_text, toggle_pause),
        pystray.MenuItem(get_lang('menu_select_area'), select_area_and_save),
        pystray.MenuItem(get_lang('menu_settings'), open_settings_window),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(get_lang('menu_exit'), quit_program)
    )
    tray_icon.title = get_lang('app_title')
    tray_icon.menu = new_menu

def main_translation_loop():
    global last_text, translator
    try:
        translator = deepl.Translator(AYARLAR['api_anahtari'])
    except Exception as e:
        print(f"HATA: DeepL Translator oluşturulamadı: {e}.")
        gui_queue.put({'type': 'show_message_error', 'title': get_lang('error_title_deepl'), 'body': get_lang('error_body_deepl_key')})
        translator = None

    with mss.mss() as sct:
        while True:
            try:
                if not ocr_allowed.is_set():
                    time.sleep(0.2)
                    continue

                if not is_paused:
                    print("-" * 30)
                    if not os.path.exists(AYARLAR['tesseract_yolu']):
                        if not is_paused: toggle_pause()
                        gui_queue.put({'type': 'show_message_error', 'title': get_lang('error_tesseract_path_title'), 'body': get_lang('error_tesseract_path_body')})
                        gui_queue.put({'type': 'open_settings'})
                        time.sleep(5)
                        continue

                    bolge = {'top': AYARLAR['top'], 'left': AYARLAR['left'], 'width': AYARLAR['width'], 'height': AYARLAR['height']}
                    if bolge['width'] < 10 or bolge['height'] < 10:
                        print("Tarama alanı seçilmemiş, bekleniyor...")
                        time.sleep(1)
                        continue

                    img = np.array(sct.grab(bolge))
                    isleme_modu = AYARLAR.get('isleme_modu', 'gri_esik')
                    print(f"Mod: {isleme_modu}")

                    if isleme_modu == 'renk_filtresi':
                        hsv_img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                        hsv_img = cv2.cvtColor(hsv_img, cv2.COLOR_BGR2HSV)
                        lower_bound = np.array([AYARLAR['renk_alt_sinir_h'], AYARLAR['renk_alt_sinir_s'], AYARLAR['renk_alt_sinir_v']])
                        upper_bound = np.array([AYARLAR['renk_ust_sinir_h'], AYARLAR['renk_ust_sinir_s'], AYARLAR['renk_ust_sinir_v']])
                        mask = cv2.inRange(hsv_img, lower_bound, upper_bound)
                        islenmis_img = cv2.bitwise_not(mask)
                        print("İşlem: Renk filtresi uygulandı ve Tesseract için ters çevrildi.")
                    else:
                        gri_img = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
                        ters_cevir = False
                        if AYARLAR['otomatik_ters_cevirme']:
                            h, w = gri_img.shape
                            kose_boyutu = min(h, w) // 4
                            kose_ortalamasi = np.mean([
                                gri_img[0:kose_boyutu, 0:kose_boyutu],
                                gri_img[0:kose_boyutu, w-kose_boyutu:w],
                                gri_img[h-kose_boyutu:h, 0:kose_boyutu],
                                gri_img[h-kose_boyutu:h, w-kose_boyutu:w]
                            ])
                            parlaklik_esigi = AYARLAR['otomatik_ters_cevirme_esigi']
                            print(f"Otomatik Ters Çevirme: Köşe parlaklığı = {kose_ortalamasi:.2f} (Eşik: {parlaklik_esigi})")
                            if kose_ortalamasi > parlaklik_esigi:
                                ters_cevir = True
                                print("İşlem: Açık zemin tespit edildi, Tesseract için ters çevirme (BINARY) uygulanacak.")
                            else:
                                print("İşlem: Koyu zemin tespit edildi, Tesseract için normal (BINARY_INV) uygulanacak.")
                        else:
                            print("İşlem: Otomatik ters çevirme kapalı.")

                        if isleme_modu == 'adaptif_esik':
                            binary_type = cv2.THRESH_BINARY if ters_cevir else cv2.THRESH_BINARY_INV
                            islenmis_img = cv2.adaptiveThreshold(gri_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, binary_type, 11, 2)
                        else:
                            binary_type = cv2.THRESH_BINARY if ters_cevir else cv2.THRESH_BINARY_INV
                            _, islenmis_img = cv2.threshold(gri_img, AYARLAR['esik_degeri'], 255, binary_type)

                    okunan_metin = pytesseract.image_to_string(islenmis_img, lang='eng')
                    temiz_metin = okunan_metin.strip().replace('\n', ' ')
                    print(f"OCR Ham Sonuç: '{temiz_metin}'")

                    if temiz_metin and len(temiz_metin) >= AYARLAR['kaynak_metin_min_uzunluk']:
                        print(f"Filtre: Minimum uzunluk ({AYARLAR['kaynak_metin_min_uzunluk']}) geçildi.")

                        benzerlik = SequenceMatcher(None, temiz_metin, last_text).ratio()
                        print(f"Benzerlik: {benzerlik:.2f} (Eşik: {AYARLAR['kaynak_metin_benzerlik_esigi']})")

                        if benzerlik < AYARLAR['kaynak_metin_benzerlik_esigi']:
                            print(">>> KARAR: YENİ METİN! Çeviriye gönderiliyor...")
                            last_text = temiz_metin
                            if translator:
                                try:
                                    if not is_paused:
                                        print(f"API'ye Gönderiliyor: '{temiz_metin}'")
                                        cevirilmis = translator.translate_text(temiz_metin, target_lang=AYARLAR['hedef_dil'])
                                        print(f"ÇEVİRİ SONUCU: '{cevirilmis.text}'")
                                        if not is_paused:
                                            gui_queue.put({'type': 'update_text', 'text': cevirilmis.text})
                                except Exception as e:
                                    print(f"Çeviri hatası: {e}")
                                    if not is_paused:
                                        gui_queue.put({'type': 'update_text', 'text': f"[{get_lang('error_translation')}]"})
                        else:
                            print(">>> KARAR: Benzer metin, çeviri atlanıyor.")

                time.sleep(AYARLAR['kontrol_araligi'])
            except Exception as e:
                print(f"Ana döngüde beklenmedik hata: {type(e).__name__} - {e}")
                time.sleep(2)

if __name__ == "__main__":
    ocr_allowed = threading.Event()
    ocr_allowed.set()

    pytesseract.pytesseract.tesseract_cmd = AYARLAR['tesseract_yolu']
    is_paused = not AYARLAR['baslangicta_baslat'] or AYARLAR['width'] < 10 or AYARLAR['height'] < 10

    hotkey_callbacks = {'register': register_hotkeys, 'update_tray': update_tray_menu, 'toggle': toggle_pause}

    gui_manager_thread = threading.Thread(target=lambda: GuiManager(gui_queue, hotkey_callbacks, ocr_allowed))
    gui_manager_thread.start()

    translation_thread = threading.Thread(target=main_translation_loop, daemon=True)
    translation_thread.start()

    register_hotkeys()

    try:
        icon_running = Image.open(get_resource_path("images/icon.png"))
        icon_stopped = Image.open(get_resource_path("images/stop.png"))
    except FileNotFoundError:
        print("HATA: İkon dosyaları bulunamadı!")
        icon_running = Image.new('RGB', (64, 64), color='red')
        icon_stopped = icon_running

    initial_icon = icon_stopped if is_paused else icon_running
    tray_icon = pystray.Icon(get_lang("app_title"), initial_icon, menu=pystray.Menu())

    update_tray_menu()

    print("Uygulama başlatıldı. Sistem tepsisi ikonunu kontrol edin.")
    tray_icon.run()

    os._exit(0)