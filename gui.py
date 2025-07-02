# gui.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
from ttkthemes import ThemedTk
import queue
import keyboard

# Diğer modüllerimizden gerekli olanları import edelim
from config_manager import (AYARLAR, get_lang, ayarlari_kaydet, arayuz_dilini_yukle,
                           get_key_from_value, DESTEKLENEN_HEDEF_DILLER,
                           DESTEKLENEN_ARAYUZ_DILLERI, get_resource_path)

class GuiManager:
    def __init__(self, gui_queue, hotkey_callbacks):
        self.gui_queue = gui_queue
        self.hotkey_callbacks = hotkey_callbacks
        
        self.root = ThemedTk(theme="arc")
        self.root.withdraw()
        self.overlay = OverlayGUI(self.root)

        # Ayarlar penceresinin modal (beklemeli) çalışmasını sağlamak için
        self.settings_window = None

        self.root.after(100, self.process_queue)
        self.root.mainloop()

    def process_queue(self):
        try:
            message = self.gui_queue.get(0)
            msg_type = message.get('type')
            
            if msg_type == 'update_text':
                self.overlay.update_text(message.get('text'))
            elif msg_type == 'open_settings':
                self.open_settings_window()
            elif msg_type == 'open_selector':
                AlanSecici(self.root)
            elif msg_type == 'show_message_info':
                messagebox.showinfo(message.get('title'), message.get('body'))
            elif msg_type == 'show_message_error':
                messagebox.showerror(message.get('title'), message.get('body'))
            elif msg_type == 'quit':
                self.root.quit()
                self.root.destroy()
                return # Döngüden çık
        except queue.Empty:
            pass
        self.root.after(100, self.process_queue)
    
    def open_settings_window(self):
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return
        
        self.settings_window = AyarlarPenceresi(self.root, self.overlay, self.hotkey_callbacks)
        self.root.wait_window(self.settings_window) # Pencere kapanana kadar bekle
        self.settings_window = None


class AyarlarPenceresi(tk.Toplevel):
    def __init__(self, master, overlay_ref, hotkey_callbacks):
        super().__init__(master)
        self.overlay = overlay_ref
        self.hotkey_callbacks = hotkey_callbacks
        
        self.title(get_lang('settings_window_title'))
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.transient(master)
        self.grab_set()

        try:
            icon_path = get_resource_path('icon.png')
            self.photo = tk.PhotoImage(file=icon_path)
            self.iconphoto(False, self.photo)
        except Exception as e:
            print(f"HATA: icon.png yüklenemedi: {e}")

        # Değişkenler
        self.var_baslangicta_baslat = tk.BooleanVar(self, value=AYARLAR['baslangicta_baslat'])
        self.var_tesseract = tk.StringVar(self, value=AYARLAR['tesseract_yolu'])
        self.var_api_key = tk.StringVar(self, value=AYARLAR['api_anahtari'])
        self.var_hedef_dil = tk.StringVar(self, value=get_key_from_value(DESTEKLENEN_HEDEF_DILLER, AYARLAR['hedef_dil']))
        self.var_arayuz_dili = tk.StringVar(self, value=DESTEKLENEN_ARAYUZ_DILLERI.get(AYARLAR['arayuz_dili']))
        self.var_font_boyutu = tk.StringVar(self, value=str(AYARLAR['font_boyutu']))
        self.var_font_rengi = tk.StringVar(self, value=AYARLAR['font_rengi'])
        self.var_bg_rengi = tk.StringVar(self, value=AYARLAR['arka_plan_rengi'])
        self.var_seffaflik = tk.StringVar(self, value=str(AYARLAR['seffaflik']))
        self.var_ust_bosluk = tk.StringVar(self, value=str(AYARLAR['ekran_ust_bosluk']))
        self.var_kontrol_araligi = tk.StringVar(self, value=str(AYARLAR['kontrol_araligi']))
        self.var_alan_sec = tk.StringVar(self, value=AYARLAR['alan_sec'])
        self.var_durdur_devam = tk.StringVar(self, value=AYARLAR['durdur_devam_et'])
        self.var_kapat = tk.StringVar(self, value=AYARLAR['programi_kapat'])
        
        self.setup_ui()

    def setup_ui(self):
        self.validate_integer = (self.register(self.sadece_sayi), '%P')
        self.validate_float = (self.register(self.sadece_ondalikli), '%P')

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")

        self.genel_tab = self.create_tab('settings_tab_general')
        self.arayuz_tab = self.create_tab('settings_tab_interface')
        self.kisayollar_tab = self.create_tab('settings_tab_hotkeys')
        
        self.populate_general_tab(self.genel_tab)
        self.populate_interface_tab(self.arayuz_tab)
        self.populate_hotkeys_tab(self.kisayollar_tab)

        button_frame = ttk.Frame(self)
        button_frame.pack(padx=10, pady=(0, 10), fill='x')
        
        self.save_button = ttk.Button(button_frame, text=get_lang('settings_button_save'), command=self.kaydet)
        self.save_button.pack(side='right', padx=5)
        self.cancel_button = ttk.Button(button_frame, text=get_lang('settings_button_cancel'), command=self.destroy)
        self.cancel_button.pack(side='right')

    # ... (populate_general_tab, populate_interface_tab, populate_hotkeys_tab vb. metodlar buraya gelecek)
    # ORİJİNAL KODDAKİ GİBİ, HİÇBİR DEĞİŞİKLİK YOK
    def sadece_sayi(self, val): return val.isdigit() or val == ""
    def sadece_ondalikli(self, val):
        if val == "" or val == ".": return True
        try: float(val); return True
        except ValueError: return False
    def create_tab(self, lang_key):
        frame = ttk.Frame(self.notebook, padding="10"); self.notebook.add(frame, text=get_lang(lang_key)); return frame
    def populate_general_tab(self, frame):
        ttk.Label(frame, text=get_lang('settings_tesseract_path')).grid(row=0, column=0, sticky='w', pady=2); ttk.Entry(frame, textvariable=self.var_tesseract, width=40).grid(row=0, column=1, sticky='ew'); ttk.Button(frame, text=get_lang('settings_button_browse'), command=lambda: self.dosya_sec(self.var_tesseract)).grid(row=0, column=2, sticky='ew', padx=(5,0))
        ttk.Label(frame, text=get_lang('settings_deepl_api_key')).grid(row=1, column=0, sticky='w', pady=2); ttk.Entry(frame, textvariable=self.var_api_key, width=50, show="*").grid(row=1, column=1, columnspan=2, sticky='ew')
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
    def dosya_sec(self, var):
        filepath = filedialog.askopenfilename(title="Tesseract.exe Seç", filetypes=[("Executable", "*.exe")]);
        if filepath: var.set(filepath)
    def renk_sec(self, var):
        mevcut_renk = var.get()
        try: self.winfo_rgb(mevcut_renk)
        except tk.TclError: mevcut_renk = "#ffffff"
        renk = colorchooser.askcolor(title=get_lang('settings_color_picker_title'), initialcolor=mevcut_renk)
        if renk and renk[1]: var.set(renk[1])

    def kaydet(self):
        # --- Veri Doğrulama ---
        try:
            seffaflik_degeri = float(self.var_seffaflik.get())
            if not (0.1 <= seffaflik_degeri <= 1.0):
                messagebox.showerror(get_lang("error_title_invalid_value"), get_lang("error_body_opacity_range"), parent=self)
                return
        except ValueError:
            messagebox.showerror(get_lang("error_title_invalid_value"), get_lang("error_body_opacity_invalid"), parent=self)
            return
        
        yeni_font_rengi = self.var_font_rengi.get()
        yeni_bg_rengi = self.var_bg_rengi.get()
        try: self.winfo_rgb(yeni_font_rengi)
        except tk.TclError:
            messagebox.showerror(get_lang("error_title_invalid_value"), get_lang("error_body_font_color_invalid", color=yeni_font_rengi), parent=self)
            return
        try: self.winfo_rgb(yeni_bg_rengi)
        except tk.TclError:
            messagebox.showerror(get_lang("error_title_invalid_value"), get_lang("error_body_bg_color_invalid", color=yeni_bg_rengi), parent=self)
            return

        # --- Ayarları Güncelleme ---
        eski_ayarlar = AYARLAR.copy()
        yeni_ayarlar = {
            'baslangicta_baslat': self.var_baslangicta_baslat.get(),
            'tesseract_yolu': self.var_tesseract.get(),
            'api_anahtari': self.var_api_key.get(),
            'hedef_dil': DESTEKLENEN_HEDEF_DILLER.get(self.var_hedef_dil.get()),
            'arayuz_dili': get_key_from_value(DESTEKLENEN_ARAYUZ_DILLERI, self.var_arayuz_dili.get()),
            'font_boyutu': int(self.var_font_boyutu.get()),
            'font_rengi': yeni_font_rengi,
            'arka_plan_rengi': yeni_bg_rengi,
            'seffaflik': float(self.var_seffaflik.get()),
            'ekran_ust_bosluk': int(self.var_ust_bosluk.get()),
            'kontrol_araligi': float(self.var_kontrol_araligi.get()),
            'alan_sec': self.var_alan_sec.get(),
            'durdur_devam_et': self.var_durdur_devam.get(),
            'programi_kapat': self.var_kapat.get()
        }
        AYARLAR.update(yeni_ayarlar)

        # --- Değişikliklerin Uygulanması ---
        ayarlari_kaydet()
        if self.overlay.winfo_exists():
            self.overlay.apply_settings()

        # Kısayol veya arayüz dili değiştiyse, ilgili güncelleme fonksiyonlarını çağır
        yeni_kisayollar = (AYARLAR['durdur_devam_et'], AYARLAR['programi_kapat'], AYARLAR['alan_sec'])
        eski_kisayollar = (eski_ayarlar['durdur_devam_et'], eski_ayarlar['programi_kapat'], eski_ayarlar['alan_sec'])
        if yeni_kisayollar != eski_kisayollar:
            self.hotkey_callbacks['register']() # main.py'deki register_hotkeys fonksiyonunu çağır

        if eski_ayarlar['arayuz_dili'] != AYARLAR['arayuz_dili']:
            arayuz_dilini_yukle(AYARLAR['arayuz_dili'])
            self.hotkey_callbacks['update_tray']() # main.py'deki update_tray_menu fonksiyonunu çağır
        
        messagebox.showinfo(get_lang('app_title'), get_lang('info_settings_saved_body'), parent=self)
        self.destroy()

class AlanSecici(tk.Toplevel):
    # ... (Bu sınıf orijinal koddaki gibi, hiçbir değişiklik yok)
    def __init__(self, master):
        super().__init__(master); self.attributes("-fullscreen", True); self.attributes("-alpha", 0.3); self.configure(bg='grey'); self.attributes("-topmost", True); self.focus_force(); self.bind("<Button-1>", self.on_mouse_press); self.bind("<B1-Motion>", self.on_mouse_drag); self.bind("<ButtonRelease-1>", self.on_mouse_release); self.bind("<Escape>", lambda e: self.destroy()); self.canvas = tk.Canvas(self, cursor="cross", bg="grey", highlightthickness=0); self.canvas.pack(fill="both", expand=True); self.rect = None; self.start_x = None; self.start_y = None; self.secilen_alan = None
    def on_mouse_press(self, event): self.start_x = self.canvas.canvasx(event.x); self.start_y = self.canvas.canvasy(event.y); self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=2)
    def on_mouse_drag(self, event): self.canvas.coords(self.rect, self.start_x, self.start_y, self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
    def on_mouse_release(self, event):
        if not self.start_x: self.destroy(); return
        end_x = self.canvas.canvasx(event.x); end_y = self.canvas.canvasy(event.y)
        x1 = int(min(self.start_x, end_x)); y1 = int(min(self.start_y, end_y)); x2 = int(max(self.start_x, end_x)); y2 = int(max(self.start_y, end_y))
        AYARLAR.update({'top': y1, 'left': x1, 'width': (x2 - x1), 'height': (y2 - y1)})
        ayarlari_kaydet() # Değişikliği anında kaydet
        self.destroy()

class OverlayGUI(tk.Toplevel):
    # ... (Bu sınıf orijinal koddaki gibi, küçük tip düzeltmeleri yapıldı)
    def __init__(self, master):
        super().__init__(master)
        self.overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.screen_width = self.winfo_screenwidth()
        self.label = tk.Label(self, text="", wraplength=self.screen_width * 0.8, justify="center", padx=15, pady=10)
        self.label.pack()
        self.apply_settings()
        self.withdraw()

    def apply_settings(self):
        self.wm_attributes("-alpha", AYARLAR['seffaflik'])
        self.config(bg=AYARLAR['arka_plan_rengi'])
        self.label.config(font=("Arial", AYARLAR['font_boyutu'], "bold"), fg=AYARLAR['font_rengi'], bg=AYARLAR['arka_plan_rengi'])

    def update_text(self, text):
        if not text:
            self.withdraw()
            return
        self.deiconify()
        self.label.config(text=text)
        self.update_idletasks()
        width = self.label.winfo_reqwidth()
        height = self.label.winfo_reqheight()
        x = (self.screen_width // 2) - (width // 2)
        y = AYARLAR['ekran_ust_bosluk']
        self.geometry(f"{width}x{height}+{x}+{y}")