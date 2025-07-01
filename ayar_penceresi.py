import tkinter as tk
from tkinter import ttk, filedialog, colorchooser, messagebox
from ttkthemes import ThemedTk
import keyboard

class AyarlarPenceresi:
    def __init__(self, mevcut_ayarlar, dil_bilgileri):
        self.mevcut_ayarlar = mevcut_ayarlar
        self.dil_bilgileri = dil_bilgileri
        self.yeni_ayarlar = None

        self.window = ThemedTk(theme="arc")
        self.window.title(self.get_lang('settings_window_title'))
        self.window.resizable(False, False); self.window.attributes("-topmost", True); self.window.focus_force()

        # DÜZELTME: Tüm değişkenler artık tk.StringVar, bu uyumluluğu garantiler.
        self.var_tesseract = tk.StringVar(value=mevcut_ayarlar.get("TESSERACT_YOLU"))
        self.var_api_key = tk.StringVar(value=mevcut_ayarlar.get("DEEPL_API_KEY"))
        self.var_hedef_dil = tk.StringVar(value=self.get_key_from_value(self.dil_bilgileri["DESTEKLENEN_HEDEF_DILLER"], mevcut_ayarlar.get("HEDEF_DIL_KODU")))
        self.var_arayuz_dili = tk.StringVar(value=self.dil_bilgileri["DESTEKLENEN_ARAYUZ_DILLER"].get(mevcut_ayarlar.get("ARAYUZ_DILI_KODU")))
        self.var_font_boyutu = tk.StringVar(value=mevcut_ayarlar.get("FONT_BOYUTU"))
        self.var_font_rengi = tk.StringVar(value=mevcut_ayarlar.get("FONT_RENGI"))
        self.var_bg_rengi = tk.StringVar(value=mevcut_ayarlar.get("ARKA_PLAN_RENGI"))
        self.var_seffaflik = tk.StringVar(value=mevcut_ayarlar.get("SEFFAFLIK"))
        self.var_ust_bosluk = tk.StringVar(value=mevcut_ayarlar.get("EKRAN_UST_BOSLUK"))
        self.var_kontrol_araligi = tk.StringVar(value=mevcut_ayarlar.get("KONTROL_ARALIGI"))
        self.var_alan_sec = tk.StringVar(value=mevcut_ayarlar.get("ALAN_SEC_TUSU"))
        self.var_durdur_devam = tk.StringVar(value=mevcut_ayarlar.get("DURDUR_DEVAM_ET_TUSU"))
        self.var_kapat = tk.StringVar(value=mevcut_ayarlar.get("PROGRAMI_KAPAT_TUSU"))

        notebook = ttk.Notebook(self.window); notebook.pack(pady=10, padx=10, expand=True, fill="both")
        self.genel_tab = self.create_tab(notebook, 'settings_tab_general'); self.arayuz_tab = self.create_tab(notebook, 'settings_tab_interface'); self.kisayollar_tab = self.create_tab(notebook, 'settings_tab_hotkeys')
        button_frame = ttk.Frame(self.window); button_frame.pack(padx=10, pady=(0, 10), fill='x')
        ttk.Button(button_frame, text=self.get_lang('settings_button_save'), command=self.kaydet).pack(side='right', padx=5)
        ttk.Button(button_frame, text=self.get_lang('settings_button_cancel'), command=self.window.destroy).pack(side='right')

    def get_lang(self, key): return self.dil_bilgileri["LANG_STRINGS"].get(key, key)
    def get_key_from_value(self, dictionary, value): return next((k for k, v in dictionary.items() if v == value), None)
    
    def create_tab(self, notebook, lang_key):
        frame = ttk.Frame(notebook, padding="10"); notebook.add(frame, text=self.get_lang(lang_key))
        if lang_key == 'settings_tab_general': self.populate_general_tab(frame)
        elif lang_key == 'settings_tab_interface': self.populate_interface_tab(frame)
        elif lang_key == 'settings_tab_hotkeys': self.populate_hotkeys_tab(frame)
        return frame
    def create_form_entry(self, parent, lang_key, var, row, **kwargs):
        ttk.Label(parent, text=self.get_lang(lang_key)).grid(row=row, column=0, sticky='w', pady=2)
        entry = ttk.Entry(parent, textvariable=var, width=50, **kwargs); entry.grid(row=row, column=1, sticky='ew', pady=2, columnspan=2); return entry
    def populate_general_tab(self, parent):
        ttk.Label(parent, text=self.get_lang('settings_tesseract_path')).grid(row=0, column=0, sticky='w', pady=2); tesseract_entry = ttk.Entry(parent, textvariable=self.var_tesseract, width=40); tesseract_entry.grid(row=0, column=1, sticky='ew'); ttk.Button(parent, text=self.get_lang('settings_button_browse'), command=lambda: self.dosya_sec(self.var_tesseract)).grid(row=0, column=2, sticky='ew', padx=(5,0))
        self.create_form_entry(parent, 'settings_deepl_api_key', self.var_api_key, 1)
        ttk.Label(parent, text=self.get_lang('settings_target_language')).grid(row=2, column=0, sticky='w', pady=2); ttk.Combobox(parent, textvariable=self.var_hedef_dil, values=list(self.dil_bilgileri["DESTEKLENEN_HEDEF_DILLER"].keys()), state="readonly").grid(row=2, column=1, sticky='ew', columnspan=2)
        ttk.Label(parent, text=self.get_lang('settings_interface_language')).grid(row=3, column=0, sticky='w', pady=2); ttk.Combobox(parent, textvariable=self.var_arayuz_dili, values=list(self.dil_bilgileri["DESTEKLENEN_ARAYUZ_DILLER"].values()), state="readonly").grid(row=3, column=1, sticky='ew', columnspan=2)
    def populate_interface_tab(self, parent):
        self.create_form_entry(parent, 'settings_font_size', self.var_font_boyutu, 0)
        ttk.Label(parent, text=self.get_lang('settings_font_color')).grid(row=1, column=0, sticky='w', pady=2); font_color_entry = ttk.Entry(parent, textvariable=self.var_font_rengi, width=40); font_color_entry.grid(row=1, column=1, sticky='ew'); ttk.Button(parent, text="...", command=lambda v=self.var_font_rengi: self.renk_sec(v), width=3).grid(row=1, column=2, sticky='ew', padx=(5,0))
        ttk.Label(parent, text=self.get_lang('settings_bg_color')).grid(row=2, column=0, sticky='w', pady=2); bg_color_entry = ttk.Entry(parent, textvariable=self.var_bg_rengi, width=40); bg_color_entry.grid(row=2, column=1, sticky='ew'); ttk.Button(parent, text="...", command=lambda v=self.var_bg_rengi: self.renk_sec(v), width=3).grid(row=2, column=2, sticky='ew', padx=(5,0))
        self.create_form_entry(parent, 'settings_opacity', self.var_seffaflik, 3) # Scale kaldırıldı, basit metin kutusu
        self.create_form_entry(parent, 'settings_top_margin', self.var_ust_bosluk, 4)
        self.create_form_entry(parent, 'settings_scan_interval', self.var_kontrol_araligi, 5)
    def populate_hotkeys_tab(self, parent):
        self.create_hotkey_entry(parent, 'settings_hotkey_select', self.var_alan_sec, 0)
        self.create_hotkey_entry(parent, 'settings_hotkey_pause', self.var_durdur_devam, 1)
        self.create_hotkey_entry(parent, 'settings_hotkey_exit', self.var_kapat, 2)
        ttk.Label(parent, text=self.get_lang('settings_hotkey_info'), style='TLabel').grid(row=3, column=0, columnspan=3, sticky='w', pady=(10,0))
    def create_hotkey_entry(self, parent, lang_key, var, row):
        ttk.Label(parent, text=self.get_lang(lang_key)).grid(row=row, column=0, sticky='w', pady=2)
        entry = ttk.Entry(parent, textvariable=var, state="readonly", justify='center'); entry.grid(row=row, column=1, sticky='ew', pady=2, columnspan=2)
        entry.bind("<Button-1>", lambda e, v=var, en=entry: self.dinlemeyi_baslat(e, v, en))
    def dinlemeyi_baslat(self, event, var, entry):
        var.set("..."); self.window.update_idletasks()
        hook = keyboard.on_press(lambda e: self.on_key_press(e, var, entry, hook), suppress=True)
    def on_key_press(self, event, var, entry, hook):
        key_name = event.name
        var.set(key_name); keyboard.unhook(hook)
    def dosya_sec(self, var):
        filepath = filedialog.askopenfilename(title="Tesseract.exe Seç", filetypes=[("Executable", "*.exe")]);
        if filepath: var.set(filepath)
    def renk_sec(self, var):
        color_code = colorchooser.askcolor(title=self.get_lang('settings_color_picker_title'));
        if color_code and color_code[1]: var.set(color_code[1])
    def kaydet(self):
        self.yeni_ayarlar = {
            "TESSERACT_YOLU": self.var_tesseract.get(), "DEEPL_API_KEY": self.var_api_key.get(),
            "HEDEF_DIL_KODU": self.dil_bilgileri["DESTEKLENEN_HEDEF_DILLER"].get(self.var_hedef_dil.get()),
            "ARAYUZ_DILI_KODU": self.get_key_from_value(self.dil_bilgileri["DESTEKLENEN_ARAYUZ_DILLER"], self.var_arayuz_dili.get()),
            "FONT_BOYUTU": self.var_font_boyutu.get(), "FONT_RENGI": self.var_font_rengi.get(),
            "ARKA_PLAN_RENGI": self.var_bg_rengi.get(), "SEFFAFLIK": self.var_seffaflik.get(),
            "EKRAN_UST_BOSLUK": self.var_ust_bosluk.get(), "KONTROL_ARALIGI": self.var_kontrol_araligi.get(),
            "DURDUR_DEVAM_ET_TUSU": self.var_durdur_devam.get(), "PROGRAMI_KAPAT_TUSU": self.var_kapat.get(), "ALAN_SEC_TUSU": self.var_alan_sec.get(),
            "altyazi_bolgesi": self.mevcut_ayarlar.get("altyazi_bolgesi")
        }
        messagebox.showinfo(self.get_lang('info_restart_required_title'), self.get_lang('info_restart_required_body'))
        self.window.destroy()
    def run(self):
        self.window.mainloop()
        return self.yeni_ayarlar