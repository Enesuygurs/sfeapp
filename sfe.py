import time, cv2, numpy as np, mss, pytesseract, deepl, tkinter as tk, threading, keyboard, os, configparser, json
from tkinter import ttk, messagebox, filedialog, colorchooser
from ttkthemes import ThemedTk
from pystray import MenuItem as item, Menu as menu
import pystray
from PIL import Image
from functools import partial

# --- (1. BÖLÜM: GLOBAL DEĞİŞKENLER VE AYAR YÖNETİMİ - DEĞİŞİKLİK YOK) ---
LANG_STRINGS = {}; DESTEKLENEN_ARAYUZ_DILLERI = {}; DESTEKLENEN_HEDEF_DILLER = {}
CONFIG_DOSYASI = 'config.ini'
config = configparser.ConfigParser()
son_metin = ""; is_paused = False; gui = None; tray_icon = None; translator = None
TESSERACT_YOLU, DEEPL_API_KEY, HEDEF_DIL_KODU, ARAYUZ_DILI_KODU = "", "", "", ""
altyazi_bolgesi = {}
FONT_BOYUTU, FONT_RENGI, ARKA_PLAN_RENGI = "20", "white", "black"
SEFFAFLIK, EKRAN_UST_BOSLUK, KONTROL_ARALIGI = "0.7", "30", "0.5"
DURDUR_DEVAM_ET_TUSU, PROGRAMI_KAPAT_TUSU, ALAN_SEC_TUSU = "f9", "f10", "f8"

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
    config['Bolge'] = {k: str(v) for k, v in altyazi_bolgesi.items()}
    config['Arayuz'] = { 'font_boyutu': FONT_BOYUTU, 'font_rengi': FONT_RENGI, 'arka_plan_rengi': ARKA_PLAN_RENGI, 'seffaflik': SEFFAFLIK, 'ekran_ust_bosluk': EKRAN_UST_BOSLUK, 'kontrol_araligi': KONTROL_ARALIGI }
    config['Kisayollar'] = { 'alan_sec': ALAN_SEC_TUSU, 'durdur_devam_et': DURDUR_DEVAM_ET_TUSU, 'programi_kapat': PROGRAMI_KAPAT_TUSU }
    with open(CONFIG_DOSYASI, 'w', encoding='utf-8') as configfile: config.write(configfile)
def ayarlari_yukle():
    global DESTEKLENEN_HEDEF_DILLER, DESTEKLENEN_ARAYUZ_DILLERI, translator, TESSERACT_YOLU, DEEPL_API_KEY, HEDEF_DIL_KODU, ARAYUZ_DILI_KODU, altyazi_bolgesi, FONT_BOYUTU, FONT_RENGI, ARKA_PLAN_RENGI, SEFFAFLIK, EKRAN_UST_BOSLUK, KONTROL_ARALIGI, DURDUR_DEVAM_ET_TUSU, PROGRAMI_KAPAT_TUSU, ALAN_SEC_TUSU
    with open('diller.json', 'r', encoding='utf-8') as f: DESTEKLENEN_HEDEF_DILLER = json.load(f)
    with open('arayuz_dilleri.json', 'r', encoding='utf-8') as f: DESTEKLENEN_ARAYUZ_DILLERI = json.load(f)
    config.read(CONFIG_DOSYASI, encoding='utf-8')
    ARAYUZ_DILI_KODU = config.get('Genel', 'arayuz_dili', fallback='TR'); arayuz_dilini_yukle(ARAYUZ_DILI_KODU)
    TESSERACT_YOLU = config.get('Genel', 'tesseract_yolu', fallback=''); DEEPL_API_KEY = config.get('Genel', 'api_anahtari', fallback=''); HEDEF_DIL_KODU = config.get('Genel', 'hedef_dil', fallback='TR')
    altyazi_bolgesi = {'top': config.get('Bolge', 'top', fallback='0'), 'left': config.get('Bolge', 'left', fallback='0'), 'width': config.get('Bolge', 'width', fallback='0'), 'height': config.get('Bolge', 'height', fallback='0')}
    FONT_BOYUTU = config.get('Arayuz', 'font_boyutu', fallback='20'); FONT_RENGI = config.get('Arayuz', 'font_rengi', fallback='white'); ARKA_PLAN_RENGI = config.get('Arayuz', 'arka_plan_rengi', fallback='black')
    SEFFAFLIK = config.get('Arayuz', 'seffaflik', fallback='0.7'); EKRAN_UST_BOSLUK = config.get('Arayuz', 'ekran_ust_bosluk', fallback='30'); KONTROL_ARALIGI = config.get('Arayuz', 'kontrol_araligi', fallback='0.5')
    DURDUR_DEVAM_ET_TUSU = config.get('Kisayollar', 'durdur_devam_et', fallback='f9'); PROGRAMI_KAPAT_TUSU = config.get('Kisayollar', 'programi_kapat', fallback='f10'); ALAN_SEC_TUSU = config.get('Kisayollar', 'alan_sec', fallback='f8')
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_YOLU
    try: translator = deepl.Translator(DEEPL_API_KEY)
    except Exception as e: print(f"DeepL Translator oluşturulamadı: {e}."); translator = None

# --------------------------------------------------------------------------------------
# 2. BÖLÜM: UYGULAMA SINIFLARI VE FONKSİYONLARI
# --------------------------------------------------------------------------------------

class AyarlarPenceresi(ThemedTk):
    # ... (Bu sınıfta değişiklik yok)
    def __init__(self):
        super().__init__(theme="arc"); self.title(get_lang('settings_window_title')); self.resizable(False, False); self.attributes("-topmost", True); self.focus_force()
        self.var_tesseract = tk.StringVar(self, value=TESSERACT_YOLU); self.var_api_key = tk.StringVar(self, value=DEEPL_API_KEY)
        self.var_hedef_dil = tk.StringVar(self, value=get_key_from_value(DESTEKLENEN_HEDEF_DILLER, HEDEF_DIL_KODU))
        self.var_arayuz_dili = tk.StringVar(self, value=DESTEKLENEN_ARAYUZ_DILLERI.get(ARAYUZ_DILI_KODU))
        self.var_font_boyutu = tk.StringVar(self, value=FONT_BOYUTU); self.var_font_rengi = tk.StringVar(self, value=FONT_RENGI)
        self.var_bg_rengi = tk.StringVar(self, value=ARKA_PLAN_RENGI); self.var_seffaflik = tk.StringVar(self, value=SEFFAFLIK)
        self.var_ust_bosluk = tk.StringVar(self, value=EKRAN_UST_BOSLUK); self.var_kontrol_araligi = tk.StringVar(self, value=KONTROL_ARALIGI)
        self.var_alan_sec = tk.StringVar(self, value=ALAN_SEC_TUSU); self.var_durdur_devam = tk.StringVar(self, value=DURDUR_DEVAM_ET_TUSU); self.var_kapat = tk.StringVar(self, value=PROGRAMI_KAPAT_TUSU)
        notebook = ttk.Notebook(self); notebook.pack(pady=10, padx=10, expand=True, fill="both")
        genel_tab = self.create_tab(notebook, 'settings_tab_general'); arayuz_tab = self.create_tab(notebook, 'settings_tab_interface'); kisayollar_tab = self.create_tab(notebook, 'settings_tab_hotkeys')
        self.populate_general_tab(genel_tab); self.populate_interface_tab(arayuz_tab); self.populate_hotkeys_tab(kisayollar_tab)
        button_frame = ttk.Frame(self); button_frame.pack(padx=10, pady=(0, 10), fill='x')
        ttk.Button(button_frame, text=get_lang('settings_button_save'), command=self.kaydet).pack(side='right', padx=5)
        ttk.Button(button_frame, text=get_lang('settings_button_cancel'), command=self.destroy).pack(side='right')
    def create_tab(self, notebook, lang_key):
        frame = ttk.Frame(notebook, padding="10"); notebook.add(frame, text=get_lang(lang_key)); return frame
    def populate_general_tab(self, frame):
        ttk.Label(frame, text=get_lang('settings_tesseract_path')).grid(row=0, column=0, sticky='w', pady=2); ttk.Entry(frame, textvariable=self.var_tesseract, width=40).grid(row=0, column=1, sticky='ew'); ttk.Button(frame, text=get_lang('settings_button_browse'), command=lambda: self.dosya_sec(self.var_tesseract)).grid(row=0, column=2, sticky='ew', padx=(5,0))
        ttk.Label(frame, text=get_lang('settings_deepl_api_key')).grid(row=1, column=0, sticky='w', pady=2); ttk.Entry(frame, textvariable=self.var_api_key, width=50).grid(row=1, column=1, columnspan=2, sticky='ew')
        ttk.Label(frame, text=get_lang('settings_target_language')).grid(row=2, column=0, sticky='w', pady=2); ttk.Combobox(frame, textvariable=self.var_hedef_dil, values=list(DESTEKLENEN_HEDEF_DILLER.keys()), state="readonly").grid(row=2, column=1, sticky='ew', columnspan=2)
        ttk.Label(frame, text=get_lang('settings_interface_language')).grid(row=3, column=0, sticky='w', pady=2); ttk.Combobox(frame, textvariable=self.var_arayuz_dili, values=list(DESTEKLENEN_ARAYUZ_DILLERI.values()), state="readonly").grid(row=3, column=1, sticky='ew', columnspan=2)
    def populate_interface_tab(self, frame):
        ttk.Label(frame, text=get_lang('settings_font_size')).grid(row=0, column=0, sticky='w', pady=2); ttk.Entry(frame, textvariable=self.var_font_boyutu).grid(row=0, column=1, columnspan=2, sticky='ew')
        ttk.Label(frame, text=get_lang('settings_font_color')).grid(row=1, column=0, sticky='w', pady=2); ttk.Entry(frame, textvariable=self.var_font_rengi, width=40).grid(row=1, column=1, sticky='ew'); ttk.Button(frame, text="...", command=lambda v=self.var_font_rengi: self.renk_sec(v), width=3).grid(row=1, column=2, sticky='ew', padx=(5,0))
        ttk.Label(frame, text=get_lang('settings_bg_color')).grid(row=2, column=0, sticky='w', pady=2); ttk.Entry(frame, textvariable=self.var_bg_rengi, width=40).grid(row=2, column=1, sticky='ew'); ttk.Button(frame, text="...", command=lambda v=self.var_bg_rengi: self.renk_sec(v), width=3).grid(row=2, column=2, sticky='ew', padx=(5,0))
        ttk.Label(frame, text=get_lang('settings_opacity')).grid(row=3, column=0, sticky='w', pady=2); ttk.Entry(frame, textvariable=self.var_seffaflik).grid(row=3, column=1, columnspan=2, sticky='ew')
        ttk.Label(frame, text=get_lang('settings_top_margin')).grid(row=4, column=0, sticky='w', pady=2); ttk.Entry(frame, textvariable=self.var_ust_bosluk).grid(row=4, column=1, columnspan=2, sticky='ew')
        ttk.Label(frame, text=get_lang('settings_scan_interval')).grid(row=5, column=0, sticky='w', pady=2); ttk.Entry(frame, textvariable=self.var_kontrol_araligi).grid(row=5, column=1, columnspan=2, sticky='ew')
    def populate_hotkeys_tab(self, frame):
        self.create_hotkey_entry(frame, 'settings_hotkey_select', self.var_alan_sec, 0); self.create_hotkey_entry(frame, 'settings_hotkey_pause', self.var_durdur_devam, 1); self.create_hotkey_entry(frame, 'settings_hotkey_exit', self.var_kapat, 2)
        ttk.Label(frame, text=get_lang('settings_hotkey_info'), style='TLabel').grid(row=3, column=0, columnspan=3, sticky='w', pady=(10,0))
    def create_hotkey_entry(self, parent, lang_key, var, row):
        ttk.Label(parent, text=get_lang(lang_key)).grid(row=row, column=0, sticky='w', pady=2)
        entry = ttk.Entry(parent, textvariable=var, state="readonly", justify='center'); entry.grid(row=row, column=1, sticky='ew', pady=2, columnspan=2)
        entry.bind("<Button-1>", lambda e, v=var: self.dinlemeyi_baslat(v))
    def dinlemeyi_baslat(self, var):
        var.set("..."); self.update_idletasks()
        try:
            event = keyboard.read_event(suppress=True)
            if event.event_type == keyboard.KEY_DOWN: var.set(event.name)
        except: pass
    def dosya_sec(self, var):
        filepath = filedialog.askopenfilename(title="Tesseract.exe Seç", filetypes=[("Executable", "*.exe")]);
        if filepath: var.set(filepath)
    def renk_sec(self, var):
        color_code = colorchooser.askcolor(title=get_lang('settings_color_picker_title'));
        if color_code and color_code[1]: var.set(color_code[1])
    def kaydet(self):
        global TESSERACT_YOLU, DEEPL_API_KEY, HEDEF_DIL_KODU, ARAYUZ_DILI_KODU, FONT_BOYUTU, FONT_RENGI, ARKA_PLAN_RENGI, SEFFAFLIK, EKRAN_UST_BOSLUK, KONTROL_ARALIGI, DURDUR_DEVAM_ET_TUSU, PROGRAMI_KAPAT_TUSU, ALAN_SEC_TUSU
        TESSERACT_YOLU = self.var_tesseract.get(); DEEPL_API_KEY = self.var_api_key.get()
        HEDEF_DIL_KODU = DESTEKLENEN_HEDEF_DILLER.get(self.var_hedef_dil.get()); ARAYUZ_DILI_KODU = get_key_from_value(DESTEKLENEN_ARAYUZ_DILLERI, self.var_arayuz_dili.get())
        FONT_BOYUTU = self.var_font_boyutu.get(); FONT_RENGI = self.var_font_rengi.get(); ARKA_PLAN_RENGI = self.var_bg_rengi.get(); SEFFAFLIK = self.var_seffaflik.get()
        EKRAN_UST_BOSLUK = self.var_ust_bosluk.get(); KONTROL_ARALIGI = self.var_kontrol_araligi.get()
        DURDUR_DEVAM_ET_TUSU = self.var_durdur_devam.get(); PROGRAMI_KAPAT_TUSU = self.var_kapat.get(); ALAN_SEC_TUSU = self.var_alan_sec.get()
        ayarlari_kaydet(); messagebox.showinfo(get_lang('info_restart_required_title'), get_lang('info_restart_required_body')); self.destroy()

def ayarlari_penceresini_ac():
    def run_settings():
        keyboard.unhook_all(); app = AyarlarPenceresi(); app.mainloop(); register_hotkeys()
    threading.Thread(target=run_settings).start()

class AlanSecici:
    def __init__(self, master):
        self.master = master; self.secim_penceresi = tk.Toplevel(self.master); self.secim_penceresi.attributes("-fullscreen", True); self.secim_penceresi.attributes("-alpha", 0.3); self.secim_penceresi.configure(bg='grey'); self.secim_penceresi.attributes("-topmost", True); self.secim_penceresi.focus_force(); self.secim_penceresi.bind("<Button-1>", self.on_mouse_press); self.secim_penceresi.bind("<B1-Motion>", self.on_mouse_drag); self.secim_penceresi.bind("<ButtonRelease-1>", self.on_mouse_release); self.secim_penceresi.bind("<Escape>", lambda e: self.secim_penceresi.destroy()); self.canvas = tk.Canvas(self.secim_penceresi, cursor="cross", bg="grey", highlightthickness=0); self.canvas.pack(fill="both", expand=True); self.rect = None; self.start_x = None; self.start_y = None; self.secilen_alan = None
    def on_mouse_press(self, event): self.start_x = self.canvas.canvasx(event.x); self.start_y = self.canvas.canvasy(event.y); self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=2)
    def on_mouse_drag(self, event): self.canvas.coords(self.rect, self.start_x, self.start_y, self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
    # DÜZELTME: on_mouse_release fonksiyonu
    def on_mouse_release(self, event):
        # Eğer sürükleme yapılmadıysa (sadece tıklandıysa), başlangıç ve bitiş noktaları aynı olabilir.
        if not self.start_x:
            self.secim_penceresi.destroy()
            return
            
        end_x = self.canvas.canvasx(event.x); end_y = self.canvas.canvasy(event.y)
        # Ondalıklı değerleri tam sayıya çevirerek hatayı önle
        x1 = int(min(self.start_x, end_x)); y1 = int(min(self.start_y, end_y))
        x2 = int(max(self.start_x, end_x)); y2 = int(max(self.start_y, end_y))
        self.secilen_alan = {'top': str(y1), 'left': str(x1), 'width': str(x2 - x1), 'height': str(y2 - y1)}
        self.secim_penceresi.destroy()
    def run(self): self.master.wait_window(self.secim_penceresi); return self.secilen_alan
    
class OverlayGUI(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        seffaflik = float(SEFFAFLIK); bg_rengi = ARKA_PLAN_RENGI; font_boyutu = int(FONT_BOYUTU); font_rengi = FONT_RENGI
        self.overrideredirect(True); self.wm_attributes("-topmost", True); self.wm_attributes("-alpha", seffaflik); self.config(bg=bg_rengi); self.screen_width = self.winfo_screenwidth(); self.label = tk.Label(self, text="", font=("Arial", font_boyutu, "bold"), fg=font_rengi, bg=bg_rengi, wraplength=self.screen_width * 0.8, justify="center", padx=15, pady=10); self.label.pack()
        self.update_text(None)
    def update_text(self, text):
        if not text: self.withdraw(); return
        self.deiconify()
        self.label.config(text=text); self.update_idletasks(); width = self.label.winfo_reqwidth(); height = self.label.winfo_reqheight(); x = (self.screen_width // 2) - (width // 2); y = int(EKRAN_UST_BOSLUK); self.geometry(f"{width}x{height}+{x}+{y}")

def register_hotkeys(): keyboard.unhook_all(); keyboard.add_hotkey(DURDUR_DEVAM_ET_TUSU, toggle_pause); keyboard.add_hotkey(PROGRAMI_KAPAT_TUSU, quit_program); keyboard.add_hotkey(ALAN_SEC_TUSU, alani_sec_ve_kaydet)
def toggle_pause(*args):
    global is_paused, son_metin
    is_paused = not is_paused
    print(f"\n--- {get_lang('console_status_paused') if is_paused else get_lang('console_status_resumed')} ---"); update_tray_menu()
    if is_paused and gui and gui.winfo_exists():
        son_metin = ""; gui.update_text(None)
def quit_program(*args): print(f"{get_lang('menu_exit')}..."); 
if tray_icon: tray_icon.stop(); os._exit(0)
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
        root = tk.Tk(); root.withdraw()
        keyboard.unhook_all(); secici = AlanSecici(root); secilen_alan = secici.run(); register_hotkeys()
        root.destroy()
        # DÜZELTME: secilen_alan'ın boş olup olmadığını kontrol et
        if secilen_alan and int(secilen_alan.get('width', 0)) > 10:
            altyazi_bolgesi.update(secilen_alan); ayarlari_kaydet()
            if is_paused: toggle_pause()
        elif not was_paused: toggle_pause()
    threading.Thread(target=do_selection).start()

def update_tray_menu():
    global tray_icon
    pause_text = get_lang('menu_resume') if is_paused else get_lang('menu_pause')
    new_menu = menu(item(pause_text, toggle_pause), item(get_lang('menu_select_area'), alani_sec_ve_kaydet), item(get_lang('menu_settings'), ayarlari_penceresini_ac), menu.SEPARATOR, item(get_lang('menu_exit'), quit_program))
    if tray_icon: tray_icon.title = get_lang('app_title'); tray_icon.menu = new_menu

def start_gui():
    global gui
    root = tk.Tk(); root.withdraw()
    gui = OverlayGUI(root)
    root.mainloop()

def main_translation_loop():
    sct = mss.mss()
    while True:
        try:
            kontrol_araligi = float(KONTROL_ARALIGI)
            if not is_paused:
                if not os.path.exists(TESSERACT_YOLU):
                    if not is_paused: toggle_pause()
                    messagebox.showerror(get_lang('error_tesseract_path_title'), get_lang('error_tesseract_path_body')); ayarlari_penceresini_ac(); continue
                bolge = {k: int(v) for k, v in altyazi_bolgesi.items()}
                ekran_goruntusu = sct.grab(bolge); img = np.array(ekran_goruntusu); gri_img = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
                _, islenmis_img = cv2.threshold(gri_img, 180, 255, cv2.THRESH_BINARY_INV)
                metin = pytesseract.image_to_string(islenmis_img, lang='eng'); temiz_metin = metin.strip().replace('\n', ' ')
                global son_metin
                if temiz_metin and temiz_metin != son_metin:
                    son_metin = temiz_metin
                    if translator:
                        try: cevirilmis = translator.translate_text(temiz_metin, target_lang=HEDEF_DIL_KODU)
                        except Exception as e: print(f"Çeviri hatası: {e}"); cevirilmis = None
                        if gui and gui.winfo_exists(): gui.update_text(cevirilmis.text if cevirilmis else "[Çeviri Hatası]")
                elif not temiz_metin and son_metin:
                    son_metin = ""
                    if gui and gui.winfo_exists(): gui.update_text("")
            time.sleep(kontrol_araligi)
        except Exception as e: print(f"Ana döngü hatası: {e}"); time.sleep(2)

# --- ANA PROGRAM BAŞLANGIÇ NOKTASI ---
if __name__ == "__main__":
    ayarlari_yukle()
    register_hotkeys()
    gui_thread = threading.Thread(target=start_gui, daemon=True); gui_thread.start()
    translation_thread = threading.Thread(target=main_translation_loop, daemon=True); translation_thread.start()
    image = Image.open("icon.png"); tray_icon = pystray.Icon(get_lang("app_title"), image)
    update_tray_menu()
    if int(altyazi_bolgesi['width']) < 10 or int(altyazi_bolgesi['height']) < 10:
        is_paused = True; update_tray_menu()
    
    print(f"--- {get_lang('app_title')} ---"); print(get_lang("console_loading_settings"))
    print("--------------------------------------------------")
    print(get_lang("console_controls_header"))
    print(f"{DURDUR_DEVAM_ET_TUSU} -> {get_lang('console_hotkey_pause')}")
    print(f"{PROGRAMI_KAPAT_TUSU} -> {get_lang('console_hotkey_exit')}")
    print(f"{ALAN_SEC_TUSU} -> {get_lang('console_hotkey_select')}")
    print("--------------------------------------------------")
    
    tray_icon.run()
    os._exit(0)