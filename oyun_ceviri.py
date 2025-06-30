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
import configparser
from pystray import MenuItem as item, Menu as menu
import pystray
from PIL import Image
from functools import partial
import json # YENİ: JSON kütüphanesini içe aktarıyoruz

# --- config.ini ve diller.json Dosyası Yönetimi ---
CONFIG_DOSYASI = 'config.ini'
DILLER_DOSYASI = 'diller.json' # YENİ: Dil dosyası adı
config = configparser.ConfigParser()
DESTEKLENEN_DILLER = {} # YENİ: Artık boş bir sözlük olarak başlıyor

def ayarlari_yukle():
    # --- diller.json dosyasını yükle veya oluştur ---
    global DESTEKLENEN_DILLER
    if not os.path.exists(DILLER_DOSYASI):
        print(f"{DILLER_DOSYASI} bulunamadı, varsayılan dillerle oluşturuluyor.")
        varsayilan_diller = {"Türkçe": "TR", "İngilizce": "EN-US", "Almanca": "DE", "Fransızca": "FR", "İspanyolca": "ES", "Japonca": "JA"}
        with open(DILLER_DOSYASI, 'w', encoding='utf-8') as f:
            json.dump(varsayilan_diller, f, ensure_ascii=False, indent=4)
    
    with open(DILLER_DOSYASI, 'r', encoding='utf-8') as f:
        DESTEKLENEN_DILLER = json.load(f)

    # --- config.ini dosyasını yükle veya oluştur ---
    if not os.path.exists(CONFIG_DOSYASI):
        # ... (config.ini oluşturma kısmı aynı) ...
        config['Genel'] = {'tesseract_yolu': r'C:\Program Files\Tesseract-OCR\tesseract.exe', 'api_anahtari': 'API_ANAHTARINIZI_BURAYA_GIRIN', 'hedef_dil': 'TR'}
        config['Bolge'] = {'top': '0', 'left': '0', 'width': '0', 'height': '0'}
        config['Arayuz'] = {'font_boyutu': '20', 'font_rengi': 'white', 'arka_plan_rengi': 'black', 'seffaflik': '0.7', 'ekran_ust_bosluk': '30', 'kontrol_araligi': '0.5'}
        config['Kisayollar'] = {'durdur_devam_et': 'f9', 'programi_kapat': 'f10', 'alan_sec': 'f8'}
        ayarlari_kaydet_config(config)
    
    config.read(CONFIG_DOSYASI, encoding='utf-8')
    # ... (Geri kalan yükleme kodları aynı) ...
    global TESSERACT_YOLU, DEEPL_API_KEY, HEDEF_DIL, altyazi_bolgesi, FONT_BOYUTU, FONT_RENGI, ARKA_PLAN_RENGI, SEFFAFLIK, EKRAN_UST_BOSLUK, KONTROL_ARALIGI, DURDUR_DEVAM_ET_TUSU, PROGRAMI_KAPAT_TUSU, ALAN_SEC_TUSU
    TESSERACT_YOLU = config.get('Genel', 'tesseract_yolu'); DEEPL_API_KEY = config.get('Genel', 'api_anahtari')
    HEDEF_DIL = config.get('Genel', 'hedef_dil', fallback='TR').upper()
    altyazi_bolgesi = {'top': config.getint('Bolge', 'top'), 'left': config.getint('Bolge', 'left'), 'width': config.getint('Bolge', 'width'), 'height': config.getint('Bolge', 'height')}
    FONT_BOYUTU = config.getint('Arayuz', 'font_boyutu'); FONT_RENGI = config.get('Arayuz', 'font_rengi'); ARKA_PLAN_RENGI = config.get('Arayuz', 'arka_plan_rengi')
    SEFFAFLIK = config.getfloat('Arayuz', 'seffaflik'); EKRAN_UST_BOSLUK = config.getint('Arayuz', 'ekran_ust_bosluk'); KONTROL_ARALIGI = config.getfloat('Arayuz', 'kontrol_araligi')
    DURDUR_DEVAM_ET_TUSU = config.get('Kisayollar', 'durdur_devam_et'); PROGRAMI_KAPAT_TUSU = config.get('Kisayollar', 'programi_kapat'); ALAN_SEC_TUSU = config.get('Kisayollar', 'alan_sec')

def ayarlari_kaydet_config(config_obj):
    with open(CONFIG_DOSYASI, 'w', encoding='utf-8') as configfile: config_obj.write(configfile)

def ayarlari_kaydet():
    config.set('Bolge', 'top', str(altyazi_bolgesi['top'])); config.set('Bolge', 'left', str(altyazi_bolgesi['left']))
    config.set('Bolge', 'width', str(altyazi_bolgesi['width'])); config.set('Bolge', 'height', str(altyazi_bolgesi['height']))
    config.set('Genel', 'hedef_dil', str(HEDEF_DIL))
    ayarlari_kaydet_config(config)

ayarlari_yukle(); pytesseract.pytesseract.tesseract_cmd = TESSERACT_YOLU
son_metin = ""; is_paused = False; gui = None; tray_icon = None
translator = deepl.Translator(DEEPL_API_KEY)
# DESTEKLENEN_DILLER sözlüğü artık koddan kaldırıldı.

def dili_degistir(dil_kodu, *args):
    global HEDEF_DIL
    if HEDEF_DIL != dil_kodu:
        HEDEF_DIL = dil_kodu; ayarlari_kaydet()
        print(f"Hedef dil {dil_kodu} olarak değiştirildi."); update_tray_menu()

# ... (toggle_pause, quit_program, update_tray_menu ve diğer tüm fonksiyonlar/sınıflar aynı kalıyor) ...
# Hiçbir değişiklik yapmanıza gerek yok, sadece kopyalayıp yapıştırın.
def toggle_pause(*args): global is_paused; is_paused = not is_paused; update_tray_menu();
if is_paused and gui: gui.update_text("")
def quit_program(*args): os._exit(0)
def update_tray_menu():
    global tray_icon, is_paused, HEDEF_DIL
    pause_text = "Devam Ettir" if is_paused else "Duraklat"
    dil_menu_items = []
    for dil_adi, dil_kodu in DESTEKLENEN_DILLER.items():
        dil_menu_items.append(
            item(dil_adi, partial(dili_degistir, dil_kodu), checked=lambda item, k=dil_kodu: HEDEF_DIL == k, radio=True)
        )
    new_menu = menu(item(pause_text, toggle_pause), item('Altyazı Alanını Seç', lambda: alani_sec_ve_kaydet()), item('Hedef Dil', menu(*dil_menu_items)), item('Çıkış', quit_program))
    if tray_icon: tray_icon.menu = new_menu
class AlanSecici:
    def __init__(self): self.root = tk.Tk(); self.root.withdraw(); self.secim_penceresi = tk.Toplevel(self.root); self.secim_penceresi.attributes("-fullscreen", True); self.secim_penceresi.attributes("-alpha", 0.3); self.secim_penceresi.configure(bg='grey'); self.secim_penceresi.attributes("-topmost", True); self.secim_penceresi.focus_force(); self.secim_penceresi.bind("<Button-1>", self.on_mouse_press); self.secim_penceresi.bind("<B1-Motion>", self.on_mouse_drag); self.secim_penceresi.bind("<ButtonRelease-1>", self.on_mouse_release); self.secim_penceresi.bind("<Escape>", lambda e: self.secim_penceresi.destroy()); self.canvas = tk.Canvas(self.secim_penceresi, cursor="cross", bg="grey", highlightthickness=0); self.canvas.pack(fill="both", expand=True); self.rect = None; self.start_x = None; self.start_y = None; self.secilen_alan = {}
    def on_mouse_press(self, event): self.start_x = self.canvas.canvasx(event.x); self.start_y = self.canvas.canvasy(event.y); self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=2)
    def on_mouse_drag(self, event): self.canvas.coords(self.rect, self.start_x, self.start_y, self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
    def on_mouse_release(self, event): end_x = self.canvas.canvasx(event.x); end_y = self.canvas.canvasy(event.y); x1 = min(self.start_x, end_x); y1 = min(self.start_y, end_y); x2 = max(self.start_x, end_x); y2 = max(self.start_y, end_y); self.secilen_alan = {'top': int(y1), 'left': int(x1), 'width': int(x2 - x1), 'height': int(y2 - y1)}; self.secim_penceresi.destroy()
    def run(self): self.root.wait_window(self.secim_penceresi); self.root.destroy(); return self.secilen_alan
def alani_sec_ve_kaydet():
    global altyazi_bolgesi, is_paused; was_paused = is_paused
    if not was_paused: toggle_pause()
    def do_selection():
        secici = AlanSecici(); secilen_alan = secici.run()
        if secilen_alan and secilen_alan['width'] > 10 and secilen_alan['height'] > 10:
            altyazi_bolgesi.update(secilen_alan); ayarlari_kaydet()
            if is_paused: toggle_pause()
        elif not was_paused: toggle_pause()
    threading.Thread(target=do_selection).start()
class OverlayGUI:
    def __init__(self): self.root = tk.Tk(); self.root.overrideredirect(True); self.root.wm_attributes("-topmost", True); self.root.wm_attributes("-alpha", SEFFAFLIK); self.root.config(bg=ARKA_PLAN_RENGI); self.screen_width = self.root.winfo_screenwidth(); self.label = tk.Label(self.root, text="", font=("Arial", FONT_BOYUTU, "bold"), fg=FONT_RENGI, bg=ARKA_PLAN_RENGI, wraplength=self.screen_width * 0.8, justify="center", padx=15, pady=10); self.label.pack()
    def update_text(self, text):
        if not text: self.root.geometry('1x1+-10+-10'); return
        self.label.config(text=text); self.root.update_idletasks(); width = self.label.winfo_reqwidth(); height = self.label.winfo_reqheight(); x = (self.screen_width // 2) - (width // 2); y = EKRAN_UST_BOSLUK; self.root.geometry(f"{width}x{height}+{x}+{y}")
    def run(self): self.root.mainloop()
def start_gui(): global gui; gui = OverlayGUI(); gui.run()
def main_translation_loop():
    sct = mss.mss(); time.sleep(2)
    while True:
        if not is_paused:
            try:
                ekran_goruntusu = sct.grab(altyazi_bolgesi); img = np.array(ekran_goruntusu); gri_img = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
                _, islenmis_img = cv2.threshold(gri_img, 180, 255, cv2.THRESH_BINARY_INV)
                metin = pytesseract.image_to_string(islenmis_img, lang='eng'); temiz_metin = metin.strip().replace('\n', ' ')
                global son_metin
                if temiz_metin and temiz_metin != son_metin:
                    son_metin = temiz_metin
                    try:
                        cevirilmis = translator.translate_text(temiz_metin, target_lang=HEDEF_DIL)
                    except Exception as e: cevirilmis = None
                    if gui and cevirilmis: gui.update_text(cevirilmis.text)
                elif not temiz_metin and son_metin: son_metin = ""; gui.update_text("")
            except Exception as e: son_metin = ""; gui.update_text("")
        time.sleep(KONTROL_ARALIGI)
if __name__ == "__main__":
    keyboard.add_hotkey(DURDUR_DEVAM_ET_TUSU, toggle_pause); keyboard.add_hotkey(PROGRAMI_KAPAT_TUSU, quit_program); keyboard.add_hotkey(ALAN_SEC_TUSU, alani_sec_ve_kaydet)
    gui_thread = threading.Thread(target=start_gui, daemon=True); gui_thread.start()
    translation_thread = threading.Thread(target=main_translation_loop, daemon=True); translation_thread.start()
    image = Image.open("icon.png")
    tray_icon = pystray.Icon("Oyun Çeviri", image, "Oyun Çeviri Aracı")
    update_tray_menu()
    if altyazi_bolgesi['width'] < 10 or altyazi_bolgesi['height'] < 10:
        is_paused = True; update_tray_menu()
    tray_icon.run()