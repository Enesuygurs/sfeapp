import time, cv2, numpy as np, mss, pytesseract, deepl, tkinter as tk, threading, keyboard, os, configparser, json, sys
from tkinter import ttk, messagebox, filedialog, colorchooser
from ttkthemes import ThemedTk
from pystray import MenuItem as item, Menu as menu
import pystray
from PIL import Image
from functools import partial
import queue

# --- (Bölüm 1 ve temel fonksiyonlar aynı) ---
LANG_STRINGS = {}; DESTEKLENEN_ARAYUZ_DILLERI = {}; DESTEKLENEN_HEDEF_DILLER = {}
CONFIG_DOSYASI = 'config.ini'; config = configparser.ConfigParser()
son_metin = ""; is_paused = False; tray_icon = None; translator = None
AYARLAR = {}
gui_queue = queue.Queue()

def get_lang(key): return LANG_STRINGS.get(key, key)
def arayuz_dilini_yukle(dil_kodu):
    global LANG_STRINGS
    try:
        with open(f"lang/{dil_kodu.lower()}.json", 'r', encoding='utf-8') as f: LANG_STRINGS = json.load(f)
    except FileNotFoundError:
        with open("lang/en.json", 'r', encoding='utf-8') as f: LANG_STRINGS = json.load(f)
def get_key_from_value(dictionary, value): return next((k for k, v in dictionary.items() if v == value), None)
def ayarlari_kaydet():
    config['Genel'] = { 'tesseract_yolu': AYARLAR['tesseract_yolu'], 'api_anahtari': AYARLAR['api_anahtari'], 'arayuz_dili': AYARLAR['arayuz_dili'], 'hedef_dil': AYARLAR['hedef_dil'], 'baslangicta_baslat': str(AYARLAR['baslangicta_baslat']) }
    config['Bolge'] = {k: str(v) for k, v in AYARLAR.items() if k in ['top', 'left', 'width', 'height']}
    config['Arayuz'] = { 'font_boyutu': AYARLAR['font_boyutu'], 'font_rengi': AYARLAR['font_rengi'], 'arka_plan_rengi': AYARLAR['arka_plan_rengi'], 'seffaflik': AYARLAR['seffaflik'], 'ekran_ust_bosluk': AYARLAR['ekran_ust_bosluk'], 'kontrol_araligi': AYARLAR['kontrol_araligi'] }
    config['Kisayollar'] = { 'alan_sec': AYARLAR['alan_sec'], 'durdur_devam_et': AYARLAR['durdur_devam_et'], 'programi_kapat': AYARLAR['programi_kapat'] }
    with open(CONFIG_DOSYASI, 'w', encoding='utf-8') as configfile: config.write(configfile)
def ayarlari_yukle():
    global DESTEKLENEN_HEDEF_DILLER, DESTEKLENEN_ARAYUZ_DILLERI, translator, AYARLAR
    with open('diller.json', 'r', encoding='utf-8') as f: DESTEKLENEN_HEDEF_DILLER = json.load(f)
    with open('arayuz_dilleri.json', 'r', encoding='utf-8') as f: DESTEKLENEN_ARAYUZ_DILLERI = json.load(f)
    config.read(CONFIG_DOSYASI, encoding='utf-8')
    AYARLAR = {
        'baslangicta_baslat': config.getboolean('Genel', 'baslangicta_baslat', fallback=True),
        'arayuz_dili': config.get('Genel', 'arayuz_dili', fallback='TR'),'tesseract_yolu': config.get('Genel', 'tesseract_yolu', fallback=''),
        'api_anahtari': config.get('Genel', 'api_anahtari', fallback=''),'hedef_dil': config.get('Genel', 'hedef_dil', fallback='TR'),
        'top': config.get('Bolge', 'top', fallback='0'), 'left': config.get('Bolge', 'left', fallback='0'),
        'width': config.get('Bolge', 'width', fallback='0'), 'height': config.get('Bolge', 'height', fallback='0'),
        'font_boyutu': config.get('Arayuz', 'font_boyutu', fallback='20'), 'font_rengi': config.get('Arayuz', 'font_rengi', fallback='white'),
        'arka_plan_rengi': config.get('Arayuz', 'arka_plan_rengi', fallback='black'), 'seffaflik': config.get('Arayuz', 'seffaflik', fallback='0.7'),
        'ekran_ust_bosluk': config.get('Arayuz', 'ekran_ust_bosluk', fallback='30'), 'kontrol_araligi': config.get('Arayuz', 'kontrol_araligi', fallback='0.5'),
        'alan_sec': config.get('Kisayollar', 'alan_sec', fallback='f8'),'durdur_devam_et': config.get('Kisayollar', 'durdur_devam_et', fallback='f9'),
        'programi_kapat': config.get('Kisayollar', 'programi_kapat', fallback='f10')
    }
    arayuz_dilini_yukle(AYARLAR['arayuz_dili'])
    pytesseract.pytesseract.tesseract_cmd = AYARLAR['tesseract_yolu']
    try: translator = deepl.Translator(AYARLAR['api_anahtari'])
    except Exception as e: print(f"DeepL Translator oluşturulamadı: {e}."); translator = None
def get_resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except Exception: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class GuiManager:
    def __init__(self):
        self.root = ThemedTk(theme="arc"); self.root.withdraw()
        self.overlay = OverlayGUI(self.root)
        self.root.after(100, self.process_queue)
        self.root.mainloop()
    def process_queue(self):
        try:
            message = gui_queue.get(0)
            msg_type = message.get('type')
            if msg_type == 'update_text': self.overlay.update_text(message.get('text'))
            elif msg_type == 'open_settings': AyarlarPenceresi(self.root, self.overlay)
            elif msg_type == 'open_selector': AlanSecici(self.root)
            elif msg_type == 'show_message_info': messagebox.showinfo(message.get('title'), message.get('body'))
            elif msg_type == 'show_message_error': messagebox.showerror(message.get('title'), message.get('body'))
        except queue.Empty: pass
        self.root.after(100, self.process_queue)

class AyarlarPenceresi(tk.Toplevel):
    def __init__(self, master, overlay_ref):
        super().__init__(master); self.overlay = overlay_ref; self.title(get_lang('settings_window_title')); self.resizable(False, False); self.attributes("-topmost", True); self.transient(master); self.grab_set()
        try:
            icon_path = get_resource_path('icon.png'); self.photo = tk.PhotoImage(file=icon_path); self.iconphoto(False, self.photo)
        except Exception as e: print(f"icon.png yüklenemedi: {e}")
        self.validate_integer = (self.register(self.sadece_sayi), '%P'); self.validate_float = (self.register(self.sadece_ondalikli), '%P')
        self.var_baslangicta_baslat = tk.BooleanVar(self, value=AYARLAR['baslangicta_baslat'])
        self.var_tesseract = tk.StringVar(self, value=AYARLAR['tesseract_yolu']); self.var_api_key = tk.StringVar(self, value=AYARLAR['api_anahtari'])
        self.var_hedef_dil = tk.StringVar(self, value=get_key_from_value(DESTEKLENEN_HEDEF_DILLER, AYARLAR['hedef_dil']))
        self.var_arayuz_dili = tk.StringVar(self, value=DESTEKLENEN_ARAYUZ_DILLERI.get(AYARLAR['arayuz_dili']))
        self.var_font_boyutu = tk.StringVar(self, value=AYARLAR['font_boyutu']); self.var_font_rengi = tk.StringVar(self, value=AYARLAR['font_rengi'])
        self.var_bg_rengi = tk.StringVar(self, value=AYARLAR['arka_plan_rengi']); self.var_seffaflik = tk.StringVar(self, value=AYARLAR['seffaflik'])
        self.var_ust_bosluk = tk.StringVar(self, value=AYARLAR['ekran_ust_bosluk']); self.var_kontrol_araligi = tk.StringVar(self, value=AYARLAR['kontrol_araligi'])
        self.var_alan_sec = tk.StringVar(self, value=AYARLAR['alan_sec']); self.var_durdur_devam = tk.StringVar(self, value=AYARLAR['durdur_devam_et']); self.var_kapat = tk.StringVar(self, value=AYARLAR['programi_kapat'])
        notebook = ttk.Notebook(self); notebook.pack(pady=10, padx=10, expand=True, fill="both")
        genel_tab = self.create_tab(notebook, 'settings_tab_general'); arayuz_tab = self.create_tab(notebook, 'settings_tab_interface'); kisayollar_tab = self.create_tab(notebook, 'settings_tab_hotkeys')
        self.populate_general_tab(genel_tab); self.populate_interface_tab(arayuz_tab); self.populate_hotkeys_tab(kisayollar_tab)
        button_frame = ttk.Frame(self); button_frame.pack(padx=10, pady=(0, 10), fill='x')
        ttk.Button(button_frame, text=get_lang('settings_button_save'), command=self.kaydet).pack(side='right', padx=5)
        ttk.Button(button_frame, text=get_lang('settings_button_cancel'), command=self.destroy).pack(side='right')
    def sadece_sayi(self, val): return val.isdigit() or val == ""
    def sadece_ondalikli(self, val):
        if val == "" or val == ".": return True
        try: float(val); return True
        except ValueError: return False
    def create_tab(self, notebook, lang_key):
        frame = ttk.Frame(notebook, padding="10"); notebook.add(frame, text=get_lang(lang_key)); return frame
    def populate_general_tab(self, frame):
        ttk.Label(frame, text=get_lang('settings_tesseract_path')).grid(row=0, column=0, sticky='w', pady=2); ttk.Entry(frame, textvariable=self.var_tesseract, width=40).grid(row=0, column=1, sticky='ew'); ttk.Button(frame, text=get_lang('settings_button_browse'), command=lambda: self.dosya_sec(self.var_tesseract)).grid(row=0, column=2, sticky='ew', padx=(5,0))
        ttk.Label(frame, text=get_lang('settings_deepl_api_key')).grid(row=1, column=0, sticky='w', pady=2); ttk.Entry(frame, textvariable=self.var_api_key, width=50).grid(row=1, column=1, columnspan=2, sticky='ew')
        ttk.Label(frame, text=get_lang('settings_target_language')).grid(row=2, column=0, sticky='w', pady=2); ttk.Combobox(frame, textvariable=self.var_hedef_dil, values=list(DESTEKLENEN_HEDEF_DILLER.keys()), state="readonly").grid(row=2, column=1, sticky='ew', columnspan=2)
        ttk.Label(frame, text=get_lang('settings_interface_language')).grid(row=3, column=0, sticky='w', pady=2); ttk.Combobox(frame, textvariable=self.var_arayuz_dili, values=list(DESTEKLENEN_ARAYUZ_DILLERI.values()), state="readonly").grid(row=3, column=1, sticky='ew', columnspan=2)
        ttk.Checkbutton(frame, text=get_lang('settings_start_on_launch'), variable=self.var_baslangicta_baslat).grid(row=4, column=0, columnspan=3, sticky='w', pady=(10,0))
    def populate_interface_tab(self, frame):
        ttk.Label(frame, text=get_lang('settings_font_size')).grid(row=0, column=0, sticky='w', pady=2); ttk.Entry(frame, textvariable=self.var_font_boyutu, validate="key", validatecommand=self.validate_integer).grid(row=0, column=1, columnspan=2, sticky='ew')
        ttk.Label(frame, text=get_lang('settings_font_color')).grid(row=1, column=0, sticky='w', pady=2); ttk.Entry(frame, textvariable=self.var_font_rengi, width=40).grid(row=1, column=1, sticky='ew'); ttk.Button(frame, text="...", command=lambda v=self.var_font_rengi: self.renk_sec(v), width=3).grid(row=1, column=2, sticky='ew', padx=(5,0))
        ttk.Label(frame, text=get_lang('settings_bg_color')).grid(row=2, column=0, sticky='w', pady=2); ttk.Entry(frame, textvariable=self.var_bg_rengi, width=40).grid(row=2, column=1, sticky='ew'); ttk.Button(frame, text="...", command=lambda v=self.var_bg_rengi: self.renk_sec(v), width=3).grid(row=2, column=2, sticky='ew', padx=(5,0))
        ttk.Label(frame, text=get_lang('settings_opacity')).grid(row=3, column=0, sticky='w', pady=2); ttk.Entry(frame, textvariable=self.var_seffaflik, validate="key", validatecommand=self.validate_float).grid(row=3, column=1, columnspan=2, sticky='ew')
        ttk.Label(frame, text=get_lang('settings_top_margin')).grid(row=4, column=0, sticky='w', pady=2); ttk.Entry(frame, textvariable=self.var_ust_bosluk, validate="key", validatecommand=self.validate_integer).grid(row=4, column=1, columnspan=2, sticky='ew')
        ttk.Label(frame, text=get_lang('settings_scan_interval')).grid(row=5, column=0, sticky='w', pady=2); ttk.Entry(frame, textvariable=self.var_kontrol_araligi, validate="key", validatecommand=self.validate_float).grid(row=5, column=1, columnspan=2, sticky='ew')
    def populate_hotkeys_tab(self, frame):
        self.create_hotkey_entry(frame, 'settings_hotkey_select', self.var_alan_sec, 0); self.create_hotkey_entry(frame, 'settings_hotkey_pause', self.var_durdur_devam, 1); self.create_hotkey_entry(frame, 'settings_hotkey_exit', self.var_kapat, 2)
        ttk.Label(frame, text=get_lang('settings_hotkey_info'), style='TLabel').grid(row=3, column=0, columnspan=3, sticky='w', pady=(10,0))
    def create_hotkey_entry(self, parent, lang_key, var, row):
        ttk.Label(parent, text=get_lang(lang_key)).grid(row=row, column=0, sticky='w', pady=2); entry = ttk.Entry(parent, textvariable=var, state="readonly", justify='center'); entry.grid(row=row, column=1, sticky='ew', pady=2, columnspan=2); entry.bind("<Button-1>", lambda e, v=var: self.dinlemeyi_baslat(v))
    def dinlemeyi_baslat(self, var):
        var.set("..."); self.update_idletasks()
        try:
            event = keyboard.read_event(suppress=True)
            if event.event_type == keyboard.KEY_DOWN: var.set(event.name)
        except: pass
    def dosya_sec(self, var): filepath = filedialog.askopenfilename(title="Tesseract.exe Seç", filetypes=[("Executable", "*.exe")]);
    def renk_sec(self, var): color_code = colorchooser.askcolor(title=get_lang('settings_color_picker_title'));
    def kaydet(self):
        global AYARLAR
        try:
            seffaflik_degeri = float(self.var_seffaflik.get())
            if not (0.1 <= seffaflik_degeri <= 1.0): messagebox.showerror("Geçersiz Değer", "Şeffaflık değeri 0.1 ile 1.0 arasında olmalıdır.", parent=self); return
        except ValueError: messagebox.showerror("Geçersiz Değer", "Şeffaflık için geçerli bir ondalıklı sayı girin.", parent=self); return
        yeni_font_rengi = self.var_font_rengi.get(); yeni_bg_rengi = self.var_bg_rengi.get()
        try: self.winfo_rgb(yeni_font_rengi)
        except tk.TclError: messagebox.showerror("Geçersiz Değer", f"'{yeni_font_rengi}' geçerli bir font rengi değil.", parent=self); return
        try: self.winfo_rgb(yeni_bg_rengi)
        except tk.TclError: messagebox.showerror("Geçersiz Değer", f"'{yeni_bg_rengi}' geçerli bir arka plan rengi değil.", parent=self); return
        yeni_ayarlar = {
            'baslangicta_baslat': self.var_baslangicta_baslat.get(),
            'tesseract_yolu': self.var_tesseract.get(), 'api_anahtari': self.var_api_key.get(),
            'hedef_dil': DESTEKLENEN_HEDEF_DILLER.get(self.var_hedef_dil.get()), 'arayuz_dili': get_key_from_value(DESTEKLENEN_ARAYUZ_DILLERI, self.var_arayuz_dili.get()),
            'font_boyutu': self.var_font_boyutu.get(), 'font_rengi': yeni_font_rengi, 'arka_plan_rengi': yeni_bg_rengi, 'seffaflik': self.var_seffaflik.get(),
            'ekran_ust_bosluk': self.var_ust_bosluk.get(), 'kontrol_araligi': self.var_kontrol_araligi.get(),
            'alan_sec': self.var_alan_sec.get(), 'durdur_devam_et': self.var_durdur_devam.get(), 'programi_kapat': self.var_kapat.get()
        }
        yeniden_baslat_gerekli = any([ AYARLAR['tesseract_yolu'] != yeni_ayarlar['tesseract_yolu'], AYARLAR['api_anahtari'] != yeni_ayarlar['api_anahtari'], AYARLAR['arayuz_dili'] != yeni_ayarlar['arayuz_dili'] ])
        AYARLAR.update(yeni_ayarlar); self.overlay.apply_settings(); ayarlari_kaydet()
        if yeniden_baslat_gerekli:
            messagebox.showinfo(get_lang('info_restart_required_title'), get_lang('info_restart_required_body'), parent=self)
        self.destroy()

class AlanSecici(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master); self.attributes("-fullscreen", True); self.attributes("-alpha", 0.3); self.configure(bg='grey'); self.attributes("-topmost", True); self.focus_force(); self.bind("<Button-1>", self.on_mouse_press); self.bind("<B1-Motion>", self.on_mouse_drag); self.bind("<ButtonRelease-1>", self.on_mouse_release); self.bind("<Escape>", lambda e: self.destroy()); self.canvas = tk.Canvas(self, cursor="cross", bg="grey", highlightthickness=0); self.canvas.pack(fill="both", expand=True); self.rect = None; self.start_x = None; self.start_y = None; self.secilen_alan = None
    def on_mouse_press(self, event): self.start_x = self.canvas.canvasx(event.x); self.start_y = self.canvas.canvasy(event.y); self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=2)
    def on_mouse_drag(self, event): self.canvas.coords(self.rect, self.start_x, self.start_y, self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
    def on_mouse_release(self, event):
        if not self.start_x: self.destroy(); return
        end_x = self.canvas.canvasx(event.x); end_y = self.canvas.canvasy(event.y)
        x1 = int(min(self.start_x, end_x)); y1 = int(min(self.start_y, end_y)); x2 = int(max(self.start_x, end_x)); y2 = int(max(self.start_y, end_y))
        self.secilen_alan = {'top': str(y1), 'left': str(x1), 'width': str(x2 - x1), 'height': str(y2 - y1)}; self.destroy()
    def run(self): self.master.wait_window(self); return self.secilen_alan

class OverlayGUI(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master); self.overrideredirect(True); self.wm_attributes("-topmost", True)
        self.screen_width = self.winfo_screenwidth()
        self.label = tk.Label(self, text="", wraplength=self.screen_width * 0.8, justify="center", padx=15, pady=10); self.label.pack()
        self.apply_settings(); self.withdraw()
    def apply_settings(self):
        self.wm_attributes("-alpha", float(AYARLAR['seffaflik'])); self.config(bg=AYARLAR['arka_plan_rengi'])
        self.label.config(font=("Arial", int(AYARLAR['font_boyutu']), "bold"), fg=AYARLAR['font_rengi'], bg=AYARLAR['arka_plan_rengi'])
    def update_text(self, text):
        if not text: self.withdraw(); return
        self.deiconify(); self.label.config(text=text); self.update_idletasks()
        width = self.label.winfo_reqwidth(); height = self.label.winfo_reqheight()
        x = (self.screen_width // 2) - (width // 2); y = int(AYARLAR['ekran_ust_bosluk']); self.geometry(f"{width}x{height}+{x}+{y}")

def register_hotkeys(): keyboard.unhook_all(); keyboard.add_hotkey(AYARLAR['durdur_devam_et'], toggle_pause); keyboard.add_hotkey(AYARLAR['programi_kapat'], quit_program); keyboard.add_hotkey(AYARLAR['alan_sec'], alani_sec_ve_kaydet)
def toggle_pause(*args):
    global is_paused, son_metin; is_paused = not is_paused; print(f"\n--- {get_lang('console_status_paused') if is_paused else get_lang('console_status_resumed')} ---"); update_tray_menu()
    if is_paused: son_metin = ""; gui_queue.put({'type': 'update_text', 'text': None})

# DÜZELTME: quit_program fonksiyonu
def quit_program(*args):
    print(f"{get_lang('menu_exit')}...");
    if tray_icon:
        tray_icon.stop()
    # os._exit(0) çağrısı ana bloğun sonuna taşındı.

def hedef_dili_degistir(dil_kodu, *args):
    if AYARLAR['hedef_dil'] != dil_kodu: AYARLAR['hedef_dil'] = dil_kodu; ayarlari_kaydet(); update_tray_menu()
def arayuz_dilini_degistir(dil_kodu, *args):
    if AYARLAR['arayuz_dili'] != dil_kodu: AYARLAR['arayuz_dili'] = dil_kodu; arayuz_dilini_yukle(dil_kodu); ayarlari_kaydet(); update_tray_menu(); gui_queue.put({'type': 'show_message_info', 'title': get_lang('info_restart_required_title'), 'body': get_lang('info_restart_required_body')})
def alani_sec_ve_kaydet():
    was_paused = is_paused;
    if not was_paused: toggle_pause()
    gui_queue.put({'type': 'open_selector'})
def ayarlari_penceresini_ac(): keyboard.unhook_all(); gui_queue.put({'type': 'open_settings'})
def update_tray_menu():
    global tray_icon; pause_text = get_lang('menu_resume') if is_paused else get_lang('menu_pause')
    new_menu = menu(item(pause_text, toggle_pause), item(get_lang('menu_select_area'), alani_sec_ve_kaydet), item(get_lang('menu_settings'), ayarlari_penceresini_ac), menu.SEPARATOR, item(get_lang('menu_exit'), quit_program))
    if tray_icon: tray_icon.title = get_lang('app_title'); tray_icon.menu = new_menu

def main_translation_loop():
    sct = mss.mss()
    while True:
        try:
            kontrol_araligi = float(AYARLAR['kontrol_araligi'])
            if not is_paused:
                if not os.path.exists(AYARLAR['tesseract_yolu']):
                    if not is_paused: toggle_pause()
                    gui_queue.put({'type': 'show_message_error', 'title': get_lang('error_tesseract_path_title'), 'body': get_lang('error_tesseract_path_body')}); gui_queue.put({'type': 'open_settings'}); continue
                bolge = { 'top': int(AYARLAR['top']), 'left': int(AYARLAR['left']), 'width': int(AYARLAR['width']), 'height': int(AYARLAR['height']) }
                ekran_goruntusu = sct.grab(bolge); img = np.array(ekran_goruntusu); gri_img = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
                _, islenmis_img = cv2.threshold(gri_img, 180, 255, cv2.THRESH_BINARY_INV)
                metin = pytesseract.image_to_string(islenmis_img, lang='eng'); temiz_metin = metin.strip().replace('\n', ' ')
                global son_metin
                if temiz_metin and temiz_metin != son_metin:
                    son_metin = temiz_metin
                    if translator:
                        try: cevirilmis = translator.translate_text(temiz_metin, target_lang=AYARLAR['hedef_dil'])
                        except Exception as e: print(f"Çeviri hatası: {e}"); cevirilmis = None
                        gui_queue.put({'type': 'update_text', 'text': cevirilmis.text if cevirilmis else "[Çeviri Hatası]"})
                elif not temiz_metin and son_metin:
                    son_metin = ""; gui_queue.put({'type': 'update_text', 'text': ""})
            time.sleep(kontrol_araligi)
        except Exception as e: print(f"Ana döngü hatası: {e}"); time.sleep(2)

# --- ANA PROGRAM BAŞLANGIÇ NOKTASI ---
if __name__ == "__main__":
    ayarlari_yukle()
    
    # DÜZELTME: Başlangıç durumu kontrolünü thread'ler başlamadan önce yap
    if not AYARLAR['baslangicta_baslat']:
        is_paused = True
    elif int(AYARLAR['width']) < 10 or int(AYARLAR['height']) < 10:
        is_paused = True
        
    gui_manager_thread = threading.Thread(target=GuiManager, daemon=True) # GUI thread'i daemon olmalı
    gui_manager_thread.start()
    
    register_hotkeys()
    translation_thread = threading.Thread(target=main_translation_loop, daemon=True)
    translation_thread.start()
    
    image = Image.open(get_resource_path("icon.png"))
    tray_icon = pystray.Icon(get_lang("app_title"), image, menu=menu())
    
    # Başlangıçta menüyü doğru halde göstermek için çağır
    update_tray_menu() 
    
    print(f"--- {get_lang('app_title')} ---"); print(get_lang("console_loading_settings"))
    print("--------------------------------------------------")
    print(get_lang("console_controls_header"))
    print(f"{AYARLAR['durdur_devam_et']} -> {get_lang('console_hotkey_pause')}")
    print(f"{AYARLAR['programi_kapat']} -> {get_lang('console_hotkey_exit')}")
    print(f"{AYARLAR['alan_sec']} -> {get_lang('console_hotkey_select')}")
    print("--------------------------------------------------")
    
    tray_icon.run() # Bu satır, quit_program'da stop() çağrılana kadar bekler.
    
    # DÜZELTME: Tray icon durduktan sonra programın tamamen kapanmasını garantile
    print("Çıkış yapılıyor...")
    os._exit(0)