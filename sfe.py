import time, cv2, numpy as np, mss, pytesseract, deepl, tkinter as tk, threading, keyboard, os, configparser, json
from tkinter import messagebox
from pystray import MenuItem as item, Menu as menu
import pystray
from PIL import Image
from functools import partial
from ayar_penceresi import AyarlarPenceresi

# --------------------------------------------------------------------------------------
# 1. BÖLÜM: GLOBAL DEĞİŞKENLER VE İLK AYAR YÜKLEME
# --------------------------------------------------------------------------------------

LANG_STRINGS = {}; DESTEKLENEN_ARAYUZ_DILLERI = {}; DESTEKLENEN_HEDEF_DILLER = {}
CONFIG_DOSYASI = 'config.ini'
config = configparser.ConfigParser()

# Global değişkenler
son_metin = ""; is_paused = False; gui = None; tray_icon = None; translator = None
TESSERACT_YOLU, DEEPL_API_KEY, HEDEF_DIL_KODU, ARAYUZ_DILI_KODU = "", "", "", ""
altyazi_bolgesi = {}
FONT_BOYUTU, FONT_RENGI, ARKA_PLAN_RENGI = 0, "", ""
SEFFAFLIK, EKRAN_UST_BOSLUK, KONTROL_ARALIGI = 0.0, 0, 0.0
DURDUR_DEVAM_ET_TUSU, PROGRAMI_KAPAT_TUSU, ALAN_SEC_TUSU = "", "", ""

# --------------------------------------------------------------------------------------
# 2. BÖLÜM: TÜM SINIF VE FONKSİYON TANIMLARI
# --------------------------------------------------------------------------------------

def get_lang(key): return LANG_STRINGS.get(key, key)
def arayuz_dilini_yukle(dil_kodu):
    global LANG_STRINGS
    try:
        with open(f"lang/{dil_kodu.lower()}.json", 'r', encoding='utf-8') as f: LANG_STRINGS = json.load(f)
    except FileNotFoundError:
        with open("lang/en.json", 'r', encoding='utf-8') as f: LANG_STRINGS = json.load(f)

def get_key_from_value(dictionary, value): return next((k for k, v in dictionary.items() if v == value), None)

def ayarlari_kaydet():
    config['Genel'] = { 'tesseract_yolu': TESSERACT_YOLU, 'api_anahtari': DEEPL_API_KEY, 'arayuz_dili': ARAYUZ_DILI_KODU, 'hedef_dil': HEDEF_DIL_KODU }
    config['Bolge'] = altyazi_bolgesi
    config['Arayuz'] = { 'font_boyutu': FONT_BOYUTU, 'font_rengi': FONT_RENGI, 'arka_plan_rengi': ARKA_PLAN_RENGI, 'seffaflik': SEFFAFLIK, 'ekran_ust_bosluk': EKRAN_UST_BOSLUK, 'kontrol_araligi': KONTROL_ARALIGI }
    config['Kisayollar'] = { 'alan_sec': ALAN_SEC_TUSU, 'durdur_devam_et': DURDUR_DEVAM_ET_TUSU, 'programi_kapat': PROGRAMI_KAPAT_TUSU }
    with open(CONFIG_DOSYASI, 'w', encoding='utf-8') as configfile: config.write(configfile)

def ayarlari_yukle():
    global DESTEKLENEN_HEDEF_DILLER, DESTEKLENEN_ARAYUZ_DILLERI, translator, TESSERACT_YOLU, DEEPL_API_KEY, HEDEF_DIL_KODU, ARAYUZ_DILI_KODU, altyazi_bolgesi, FONT_BOYUTU, FONT_RENGI, ARKA_PLAN_RENGI, SEFFAFLIK, EKRAN_UST_BOSLUK, KONTROL_ARALIGI, DURDUR_DEVAM_ET_TUSU, PROGRAMI_KAPAT_TUSU, ALAN_SEC_TUSU
    with open('diller.json', 'r', encoding='utf-8') as f: DESTEKLENEN_HEDEF_DILLER = json.load(f)
    with open('arayuz_dilleri.json', 'r', encoding='utf-8') as f: DESTEKLENEN_ARAYUZ_DILLERI = json.load(f)
    config.read(CONFIG_DOSYASI, encoding='utf-8')
    ARAYUZ_DILI_KODU = config.get('Genel', 'arayuz_dili', fallback='EN').upper(); arayuz_dilini_yukle(ARAYUZ_DILI_KODU)
    TESSERACT_YOLU = config.get('Genel', 'tesseract_yolu'); DEEPL_API_KEY = config.get('Genel', 'api_anahtari'); HEDEF_DIL_KODU = config.get('Genel', 'hedef_dil', fallback='TR').upper()
    altyazi_bolgesi = {'top': config.getint('Bolge', 'top'), 'left': config.getint('Bolge', 'left'), 'width': config.getint('Bolge', 'width'), 'height': config.getint('Bolge', 'height')}
    FONT_BOYUTU = config.getint('Arayuz', 'font_boyutu'); FONT_RENGI = config.get('Arayuz', 'font_rengi'); ARKA_PLAN_RENGI = config.get('Arayuz', 'arka_plan_rengi'); SEFFAFLIK = config.getfloat('Arayuz', 'seffaflik'); EKRAN_UST_BOSLUK = config.getint('Arayuz', 'ekran_ust_bosluk'); KONTROL_ARALIGI = config.getfloat('Arayuz', 'kontrol_araligi')
    DURDUR_DEVAM_ET_TUSU = config.get('Kisayollar', 'durdur_devam_et'); PROGRAMI_KAPAT_TUSU = config.get('Kisayollar', 'programi_kapat'); ALAN_SEC_TUSU = config.get('Kisayollar', 'alan_sec')
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_YOLU
    try: translator = deepl.Translator(DEEPL_API_KEY)
    except Exception as e: print(f"DeepL Translator oluşturulamadı: {e}."); translator = None

def ayarlari_penceresini_ac():
    def run_settings():
        keyboard.unhook_all()
        mevcut_ayarlar = { "TESSERACT_YOLU": TESSERACT_YOLU, "DEEPL_API_KEY": DEEPL_API_KEY, "HEDEF_DIL_KODU": HEDEF_DIL_KODU, "ARAYUZ_DILI_KODU": ARAYUZ_DILI_KODU, "FONT_BOYUTU": FONT_BOYUTU, "FONT_RENGI": FONT_RENGI, "ARKA_PLAN_RENGI": ARKA_PLAN_RENGI, "SEFFAFLIK": SEFFAFLIK, "EKRAN_UST_BOSLUK": EKRAN_UST_BOSLUK, "KONTROL_ARALIGI": KONTROL_ARALIGI, "ALAN_SEC_TUSU": ALAN_SEC_TUSU, "DURDUR_DEVAM_ET_TUSU": DURDUR_DEVAM_ET_TUSU, "PROGRAMI_KAPAT_TUSU": PROGRAMI_KAPAT_TUSU, "altyazi_bolgesi": altyazi_bolgesi }
        dil_bilgileri = { "LANG_STRINGS": LANG_STRINGS, "DESTEKLENEN_HEDEF_DILLER": DESTEKLENEN_HEDEF_DILLER, "DESTEKLENEN_ARAYUZ_DILLER": DESTEKLENEN_ARAYUZ_DILLERI }
        
        # DÜZELTME: AyarlarPenceresi'ni başlatırken argümanları doğru bir şekilde gönderiyoruz.
        app = AyarlarPenceresi(mevcut_ayarlar, dil_bilgileri)
        yeni_ayarlar = app.run()

        if yeni_ayarlar:
            for key, value in yeni_ayarlar.items():
                if key in globals(): globals()[key] = value
            ayarlari_kaydet()
        
        register_hotkeys()
    threading.Thread(target=run_settings).start()

class AlanSecici:
    def __init__(self): self.root = tk.Tk(); self.root.withdraw(); self.secim_penceresi = tk.Toplevel(self.root); self.secim_penceresi.attributes("-fullscreen", True); self.secim_penceresi.attributes("-alpha", 0.3); self.secim_penceresi.configure(bg='grey'); self.secim_penceresi.attributes("-topmost", True); self.secim_penceresi.focus_force(); self.secim_penceresi.bind("<Button-1>", self.on_mouse_press); self.secim_penceresi.bind("<B1-Motion>", self.on_mouse_drag); self.secim_penceresi.bind("<ButtonRelease-1>", self.on_mouse_release); self.secim_penceresi.bind("<Escape>", lambda e: self.secim_penceresi.destroy()); self.canvas = tk.Canvas(self.secim_penceresi, cursor="cross", bg="grey", highlightthickness=0); self.canvas.pack(fill="both", expand=True); self.rect = None; self.start_x = None; self.start_y = None; self.secilen_alan = {}
    def on_mouse_press(self, event): self.start_x = self.canvas.canvasx(event.x); self.start_y = self.canvas.canvasy(event.y); self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=2)
    def on_mouse_drag(self, event): self.canvas.coords(self.rect, self.start_x, self.start_y, self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
    def on_mouse_release(self, event): end_x = self.canvas.canvasx(event.x); end_y = self.canvas.canvasy(event.y); x1 = min(self.start_x, end_x); y1 = min(self.start_y, end_y); x2 = max(self.start_x, end_x); y2 = max(self.start_y, end_y); self.secilen_alan = {'top': int(y1), 'left': int(x1), 'width': int(x2 - x1), 'height': int(y2 - y1)}; self.secim_penceresi.destroy()
    def run(self): self.root.wait_window(self.secim_penceresi); self.root.destroy(); return self.secilen_alan

class OverlayGUI:
    def __init__(self): self.root = tk.Tk(); self.root.overrideredirect(True); self.root.wm_attributes("-topmost", True); self.root.wm_attributes("-alpha", SEFFAFLIK); self.root.config(bg=ARKA_PLAN_RENGI); self.screen_width = self.root.winfo_screenwidth(); self.label = tk.Label(self.root, text="", font=("Arial", FONT_BOYUTU, "bold"), fg=FONT_RENGI, bg=ARKA_PLAN_RENGI, wraplength=self.screen_width * 0.8, justify="center", padx=15, pady=10); self.label.pack()
    def update_text(self, text):
        if not text: self.root.geometry('1x1+-10+-10'); return
        self.label.config(text=text); self.root.update_idletasks(); width = self.label.winfo_reqwidth(); height = self.label.winfo_reqheight(); x = (self.screen_width // 2) - (width // 2); y = EKRAN_UST_BOSLUK; self.root.geometry(f"{width}x{height}+{x}+{y}")
    def run(self): self.root.mainloop()

def register_hotkeys(): keyboard.unhook_all(); keyboard.add_hotkey(DURDUR_DEVAM_ET_TUSU, toggle_pause); keyboard.add_hotkey(PROGRAMI_KAPAT_TUSU, quit_program); keyboard.add_hotkey(ALAN_SEC_TUSU, alani_sec_ve_kaydet)
def toggle_pause(*args): global is_paused; is_paused = not is_paused; print(f"\n--- {get_lang('console_status_paused') if is_paused else get_lang('console_status_resumed')} ---"); update_tray_menu()

# DÜZELTME: quit_program fonksiyonu os._exit(0) kullanacak şekilde güncellendi.
def quit_program(*args):
    print(f"{get_lang('menu_exit')}...");
    if tray_icon: tray_icon.visible = False; tray_icon.stop()
    os._exit(0)

def hedef_dili_degistir(dil_kodu, *args):
    global HEDEF_DIL_KODU
    if HEDEF_DIL_KODU != dil_kodu: HEDEF_DIL_KODU = dil_kodu; ayarlari_kaydet(); update_tray_menu()
def arayuz_dilini_degistir(dil_kodu, *args):
    global ARAYUZ_DILI_KODU
    if ARAYUZ_DILI_KODU != dil_kodu: ARAYUZ_DILI_KODU = dil_kodu; arayuz_dilini_yukle(dil_kodu); ayarlari_kaydet(); update_tray_menu(); messagebox.showinfo(get_lang('info_restart_required_title'), get_lang('info_restart_required_body'))
def alani_sec_ve_kaydet():
    global altyazi_bolgesi, is_paused; was_paused = is_paused
    if not was_paused: toggle_pause()
    def do_selection():
        keyboard.unhook_all(); secici = AlanSecici(); secilen_alan = secici.run(); register_hotkeys()
        if secilen_alan and secilen_alan['width'] > 10 and secilen_alan['height'] > 10:
            altyazi_bolgesi.update(secilen_alan); ayarlari_kaydet()
            if is_paused: toggle_pause()
        elif not was_paused: toggle_pause()
    threading.Thread(target=do_selection).start()

def update_tray_menu():
    global tray_icon
    pause_text = get_lang('menu_resume') if is_paused else get_lang('menu_pause')
    hedef_dil_items = [item(dil_adi, partial(hedef_dili_degistir, dil_kodu), checked=lambda item, k=dil_kodu: HEDEF_DIL_KODU == k, radio=True) for dil_adi, dil_kodu in DESTEKLENEN_HEDEF_DILLER.items()]
    arayuz_dil_items = [item(dil_adi, partial(arayuz_dilini_degistir, dil_kodu), checked=lambda item, k=dil_kodu: ARAYUZ_DILI_KODU == k, radio=True) for dil_kodu, dil_adi in DESTEKLENEN_ARAYUZ_DILLERI.items()]
    new_menu = menu(
        item(pause_text, toggle_pause),
        item(get_lang('menu_select_area'), alani_sec_ve_kaydet),
        item(get_lang('menu_settings'), ayarlari_penceresini_ac),
        item(get_lang('menu_target_language'), menu(*hedef_dil_items)),
        item(get_lang('menu_interface_language'), menu(*arayuz_dil_items)),
        item(get_lang('menu_exit'), quit_program)
    )
    if tray_icon: tray_icon.title = get_lang('app_title'); tray_icon.menu = new_menu

def start_gui(): global gui; gui = OverlayGUI(); gui.run()

def main_translation_loop():
    sct = mss.mss()
    while True:
        if not is_paused:
            try:
                if not os.path.exists(TESSERACT_YOLU):
                    if not is_paused: toggle_pause()
                    messagebox.showerror(get_lang('error_tesseract_path_title'), get_lang('error_tesseract_path_body')); ayarlari_penceresini_ac(); continue
                ekran_goruntusu = sct.grab(altyazi_bolgesi); img = np.array(ekran_goruntusu); gri_img = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
                _, islenmis_img = cv2.threshold(gri_img, 180, 255, cv2.THRESH_BINARY_INV)
                metin = pytesseract.image_to_string(islenmis_img, lang='eng'); temiz_metin = metin.strip().replace('\n', ' ')
                global son_metin
                if temiz_metin and temiz_metin != son_metin:
                    son_metin = temiz_metin
                    if translator:
                        try: cevirilmis = translator.translate_text(temiz_metin, target_lang=HEDEF_DIL_KODU)
                        except Exception as e: print(f"Çeviri hatası: {e}"); cevirilmis = None
                        if gui and cevirilmis: gui.update_text(cevirilmis.text)
                elif not temiz_metin and son_metin: son_metin = ""; gui.update_text("")
            except Exception as e: son_metin = ""; print(f"Ana döngü hatası: {e}")
        time.sleep(KONTROL_ARALIGI)

# --------------------------------------------------------------------------------------
# 3. BÖLÜM: ANA PROGRAM BAŞLANGIÇ NOKTASI
# --------------------------------------------------------------------------------------

if __name__ == "__main__":
    ayarlari_yukle()
    register_hotkeys()
    gui_thread = threading.Thread(target=start_gui, daemon=True); gui_thread.start()
    translation_thread = threading.Thread(target=main_translation_loop, daemon=True); translation_thread.start()
    image = Image.open("icon.png"); tray_icon = pystray.Icon("app_name", image)
    update_tray_menu()
    if altyazi_bolgesi['width'] < 10 or altyazi_bolgesi['height'] < 10:
        is_paused = True; update_tray_menu()
    
    print(f"--- {get_lang('app_title')} ---"); print(get_lang("console_loading_settings"))
    print("--------------------------------------------------")
    print(get_lang("console_controls_header"))
    print(f"{DURDUR_DEVAM_ET_TUSU} -> {get_lang('console_hotkey_pause')}")
    print(f"{PROGRAMI_KAPAT_TUSU} -> {get_lang('console_hotkey_exit')}")
    print(f"{ALAN_SEC_TUSU} -> {get_lang('console_hotkey_select')}")
    print("--------------------------------------------------")
    
    tray_icon.run()