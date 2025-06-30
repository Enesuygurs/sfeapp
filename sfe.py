import time, cv2, numpy as np, mss, pytesseract, deepl, tkinter as tk, threading, keyboard, os, configparser, json
from pystray import MenuItem as item, Menu as menu
import pystray
from PIL import Image
from functools import partial

# --- Global Değişkenler ve Fonksiyonlar ---
LANG_STRINGS = {}
DESTEKLENEN_ARAYUZ_DILLERI = {}
DESTEKLENEN_HEDEF_DILLER = {}

def get_lang(key): return LANG_STRINGS.get(key, key)

def arayuz_dilini_yukle(dil_kodu):
    global LANG_STRINGS
    try:
        with open(f"lang/{dil_kodu.lower()}.json", 'r', encoding='utf-8') as f:
            LANG_STRINGS = json.load(f)
    except FileNotFoundError:
        print(f"Dil dosyası bulunamadı: lang/{dil_kodu.lower()}.json. İngilizce'ye (EN) geçiliyor.")
        with open("lang/en.json", 'r', encoding='utf-8') as f:
            LANG_STRINGS = json.load(f)

# --- Ayar ve Veri Yönetimi ---
CONFIG_DOSYASI = 'config.ini'
HEDEF_DILLER_DOSYASI = 'diller.json'
ARAYUZ_DILLERI_DOSYASI = 'arayuz_dilleri.json'
config = configparser.ConfigParser()

def ayarlari_yukle():
    global DESTEKLENEN_HEDEF_DILLER, DESTEKLENEN_ARAYUZ_DILLERI
    with open(HEDEF_DILLER_DOSYASI, 'r', encoding='utf-8') as f:
        DESTEKLENEN_HEDEF_DILLER = json.load(f)
    with open(ARAYUZ_DILLERI_DOSYASI, 'r', encoding='utf-8') as f:
        DESTEKLENEN_ARAYUZ_DILLERI = json.load(f)
    config.read(CONFIG_DOSYASI, encoding='utf-8')
    global TESSERACT_YOLU, DEEPL_API_KEY, HEDEF_DIL, ARAYUZ_DILI, altyazi_bolgesi, FONT_BOYUTU, FONT_RENGI, ARKA_PLAN_RENGI, SEFFAFLIK, EKRAN_UST_BOSLUK, KONTROL_ARALIGI, DURDUR_DEVAM_ET_TUSU, PROGRAMI_KAPAT_TUSU, ALAN_SEC_TUSU
    ARAYUZ_DILI = config.get('Genel', 'arayuz_dili', fallback='EN').upper()
    arayuz_dilini_yukle(ARAYUZ_DILI)
    TESSERACT_YOLU = config.get('Genel', 'tesseract_yolu'); DEEPL_API_KEY = config.get('Genel', 'api_anahtari')
    HEDEF_DIL = config.get('Genel', 'hedef_dil', fallback='TR').upper()
    altyazi_bolgesi = {'top': config.getint('Bolge', 'top'), 'left': config.getint('Bolge', 'left'), 'width': config.getint('Bolge', 'width'), 'height': config.getint('Bolge', 'height')}
    FONT_BOYUTU = config.getint('Arayuz', 'font_boyutu'); FONT_RENGI = config.get('Arayuz', 'font_rengi'); ARKA_PLAN_RENGI = config.get('Arayuz', 'arka_plan_rengi')
    SEFFAFLIK = config.getfloat('Arayuz', 'seffaflik'); EKRAN_UST_BOSLUK = config.getint('Arayuz', 'ekran_ust_bosluk'); KONTROL_ARALIGI = config.getfloat('Arayuz', 'kontrol_araligi')
    DURDUR_DEVAM_ET_TUSU = config.get('Kisayollar', 'durdur_devam_et'); PROGRAMI_KAPAT_TUSU = config.get('Kisayollar', 'programi_kapat'); ALAN_SEC_TUSU = config.get('Kisayollar', 'alan_sec')

def ayarlari_kaydet():
    config.set('Genel', 'arayuz_dili', str(ARAYUZ_DILI)); config.set('Genel', 'hedef_dil', str(HEDEF_DIL))
    config.set('Bolge', 'top', str(altyazi_bolgesi['top'])); config.set('Bolge', 'left', str(altyazi_bolgesi['left']))
    config.set('Bolge', 'width', str(altyazi_bolgesi['width'])); config.set('Bolge', 'height', str(altyazi_bolgesi['height']))
    with open(CONFIG_DOSYASI, 'w', encoding='utf-8') as configfile: config.write(configfile)

# --- Uygulama Fonksiyonları ---
son_metin = ""; is_paused = False; gui = None; tray_icon = None

def hedef_dili_degistir(dil_kodu, *args):
    global HEDEF_DIL
    if HEDEF_DIL != dil_kodu: HEDEF_DIL = dil_kodu; ayarlari_kaydet(); update_tray_menu()

def arayuz_dilini_degistir(dil_kodu, *args):
    global ARAYUZ_DILI
    if ARAYUZ_DILI != dil_kodu: ARAYUZ_DILI = dil_kodu; arayuz_dilini_yukle(dil_kodu); ayarlari_kaydet(); update_tray_menu()

def toggle_pause(*args):
    global is_paused; is_paused = not is_paused
    print(f"\n--- {get_lang('console_status_paused') if is_paused else get_lang('console_status_resumed')} ---")
    update_tray_menu();
    if is_paused and gui: gui.update_text("")

def quit_program(*args): os._exit(0)

def update_tray_menu():
    global tray_icon
    pause_text = get_lang('menu_resume') if is_paused else get_lang('menu_pause')
    
    hedef_dil_items = []
    # DÜZELTME: Değişken adları doğru sıraya konuldu. (anahtar, değer) -> (dil_adi, dil_kodu)
    for dil_adi, dil_kodu in DESTEKLENEN_HEDEF_DILLER.items():
        hedef_dil_items.append(item(dil_adi, partial(hedef_dili_degistir, dil_kodu), checked=lambda item, k=dil_kodu: HEDEF_DIL == k, radio=True))
        
    arayuz_dil_items = []
    for dil_kodu, dil_adi in DESTEKLENEN_ARAYUZ_DILLERI.items():
        arayuz_dil_items.append(item(dil_adi, partial(arayuz_dilini_degistir, dil_kodu), checked=lambda item, k=dil_kodu: ARAYUZ_DILI == k, radio=True))
    
    new_menu = menu(
        item(pause_text, toggle_pause),
        item(get_lang('menu_select_area'), lambda: alani_sec_ve_kaydet()),
        item(get_lang('menu_target_language'), menu(*hedef_dil_items)),
        item(get_lang('menu_interface_language'), menu(*arayuz_dil_items)),
        item(get_lang('menu_exit'), quit_program)
    )
    if tray_icon:
        tray_icon.title = get_lang('app_title')
        tray_icon.menu = new_menu

# ... (Geri kalan tüm kodlar aynı, değişiklik yok) ...
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
    sct = mss.mss(); translator = deepl.Translator(DEEPL_API_KEY)
    while True:
        if not is_paused:
            try:
                ekran_goruntusu = sct.grab(altyazi_bolgesi); img = np.array(ekran_goruntusu); gri_img = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
                _, islenmis_img = cv2.threshold(gri_img, 180, 255, cv2.THRESH_BINARY_INV)
                metin = pytesseract.image_to_string(islenmis_img, lang='eng'); temiz_metin = metin.strip().replace('\n', ' ')
                global son_metin
                if temiz_metin and temiz_metin != son_metin:
                    son_metin = temiz_metin
                    try: cevirilmis = translator.translate_text(temiz_metin, target_lang=HEDEF_DIL)
                    except Exception as e: cevirilmis = None
                    if gui and cevirilmis: gui.update_text(cevirilmis.text)
                elif not temiz_metin and son_metin: son_metin = ""; gui.update_text("")
            except Exception as e: son_metin = ""; gui.update_text("")
        time.sleep(KONTROL_ARALIGI)

if __name__ == "__main__":
    ayarlari_yukle(); pytesseract.pytesseract.tesseract_cmd = TESSERACT_YOLU
    keyboard.add_hotkey(DURDUR_DEVAM_ET_TUSU, toggle_pause); keyboard.add_hotkey(PROGRAMI_KAPAT_TUSU, quit_program); keyboard.add_hotkey(ALAN_SEC_TUSU, alani_sec_ve_kaydet)
    gui_thread = threading.Thread(target=start_gui, daemon=True); gui_thread.start()
    translation_thread = threading.Thread(target=main_translation_loop, daemon=True); translation_thread.start()
    image = Image.open("icon.png"); tray_icon = pystray.Icon("app_name", image)
    update_tray_menu()
    if altyazi_bolgesi['width'] < 10 or altyazi_bolgesi['height'] < 10:
        is_paused = True; update_tray_menu()
    
    print("--------------------------------------------------")
    print(get_lang("console_controls_header"))
    print(f"{DURDUR_DEVAM_ET_TUSU} -> {get_lang('console_hotkey_pause')}")
    print(f"{PROGRAMI_KAPAT_TUSU} -> {get_lang('console_hotkey_exit')}")
    print(f"{ALAN_SEC_TUSU} -> {get_lang('console_hotkey_select')}")
    print("--------------------------------------------------")
    
    tray_icon.run()