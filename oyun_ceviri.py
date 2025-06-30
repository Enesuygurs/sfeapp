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
from pystray import MenuItem as item
import pystray
from PIL import Image
from pynput import mouse # YENİ: Fare olaylarını dinlemek için

# --- config.ini Dosyası Yönetimi ---
CONFIG_DOSYASI = 'config.ini'
config = configparser.ConfigParser()

def ayarlari_yukle():
    config.read(CONFIG_DOSYASI, encoding='utf-8')
    # Ayarları global değişkenlere yükle
    global TESSERACT_YOLU, DEEPL_API_KEY, altyazi_bolgesi, FONT_BOYUTU, FONT_RENGI, ARKA_PLAN_RENGI, SEFFAFLIK, EKRAN_UST_BOSLUK, KONTROL_ARALIGI, DURDUR_DEVAM_ET_TUSU, PROGRAMI_KAPAT_TUSU, ALAN_SEC_TUSU
    TESSERACT_YOLU = config.get('Genel', 'tesseract_yolu')
    DEEPL_API_KEY = config.get('Genel', 'api_anahtari')
    altyazi_bolgesi = {'top': config.getint('Bolge', 'top'), 'left': config.getint('Bolge', 'left'), 'width': config.getint('Bolge', 'width'), 'height': config.getint('Bolge', 'height')}
    FONT_BOYUTU = config.getint('Arayuz', 'font_boyutu')
    FONT_RENGI = config.get('Arayuz', 'font_rengi')
    ARKA_PLAN_RENGI = config.get('Arayuz', 'arka_plan_rengi')
    SEFFAFLIK = config.getfloat('Arayuz', 'seffaflik')
    EKRAN_UST_BOSLUK = config.getint('Arayuz', 'ekran_ust_bosluk')
    KONTROL_ARALIGI = config.getfloat('Arayuz', 'kontrol_araligi')
    DURDUR_DEVAM_ET_TUSU = config.get('Kisayollar', 'durdur_devam_et')
    PROGRAMI_KAPAT_TUSU = config.get('Kisayollar', 'programi_kapat')
    ALAN_SEC_TUSU = config.get('Kisayollar', 'alan_sec') # YENİ: Alan seçme tuşu

def ayarlari_kaydet():
    # Güncel koordinatları config nesnesine yaz
    config.set('Bolge', 'top', str(altyazi_bolgesi['top']))
    config.set('Bolge', 'left', str(altyazi_bolgesi['left']))
    config.set('Bolge', 'width', str(altyazi_bolgesi['width']))
    config.set('Bolge', 'height', str(altyazi_bolgesi['height']))
    # Dosyaya kaydet
    with open(CONFIG_DOSYASI, 'w', encoding='utf-8') as configfile:
        config.write(configfile)
    print("Yeni altyazı bölgesi kaydedildi.")

# --- İlk Yükleme ---
ayarlari_yukle()
pytesseract.pytesseract.tesseract_cmd = TESSERACT_YOLU

# --- Global Değişkenler ve Fonksiyonlar ---
# ... (Öncekiyle aynı, değişiklik yok) ...
son_metin = ""
is_paused = False
translator = deepl.Translator(DEEPL_API_KEY)
gui = None
tray_icon = None

def toggle_pause():
    global is_paused
    is_paused = not is_paused
    update_tray_menu()
    if is_paused and gui:
        gui.update_text("")

def quit_program():
    if tray_icon: tray_icon.stop()
    if gui: gui.root.quit()
    os._exit(0)

def update_tray_menu():
    global tray_icon, is_paused
    pause_text = "Devam Ettir" if is_paused else "Duraklat"
    new_menu = pystray.Menu(
        item(pause_text, toggle_pause),
        item('Altyazı Alanını Seç', alani_sec_ve_kaydet), # YENİ: Menüye eklendi
        item('Çıkış', quit_program)
    )
    if tray_icon: tray_icon.menu = new_menu

# --- YENİ: Alan Seçme Sınıfı ve Fonksiyonları ---
class AlanSecici:
    def __init__(self, parent):
        self.parent = parent
        self.parent.withdraw() # Ana pencereyi gizle
        self.secim_penceresi = tk.Toplevel(self.parent)
        self.secim_penceresi.attributes("-fullscreen", True)
        self.secim_penceresi.attributes("-alpha", 0.3)
        self.secim_penceresi.configure(bg='grey')
        self.secim_penceresi.bind("<Button-1>", self.on_mouse_press)
        self.secim_penceresi.bind("<B1-Motion>", self.on_mouse_drag)
        self.secim_penceresi.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.canvas = tk.Canvas(self.secim_penceresi, cursor="cross", bg="grey", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.rect = None
        self.start_x = None
        self.start_y = None
        self.secilen_alan = {}

    def on_mouse_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        if not self.rect:
            self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=2)

    def on_mouse_drag(self, event):
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_mouse_release(self, event):
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)
        self.secilen_alan = {'top': int(y1), 'left': int(x1), 'width': int(x2 - x1), 'height': int(y2 - y1)}
        self.secim_penceresi.destroy()
        self.parent.deiconify() # Ana pencereyi geri göster

def alani_sec_ve_kaydet():
    global altyazi_bolgesi, is_paused
    was_paused = is_paused
    if not was_paused:
        toggle_pause() # Alan seçimi sırasında çeviriyi duraklat
    
    # GUI thread'inde bu işlemi güvenli bir şekilde yapmak için `call_soon_threadsafe` kullanıyoruz.
    def do_selection():
        root = tk.Tk()
        secici = AlanSecici(root)
        root.wait_window(secici.secim_penceresi) # Seçim bitene kadar bekle
        if secici.secilen_alan:
            altyazi_bolgesi.update(secici.secilen_alan)
            ayarlari_kaydet()
        root.destroy()
        if not was_paused:
            toggle_pause() # Eski durumuna geri dön

    threading.Thread(target=do_selection).start()

# --- OverlayGUI, start_gui ve main_translation_loop ---
# Bu bölümlerde hiçbir değişiklik yok, önceki kodla aynılar.
class OverlayGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True); self.root.wm_attributes("-topmost", True); self.root.wm_attributes("-alpha", SEFFAFLIK); self.root.config(bg=ARKA_PLAN_RENGI)
        self.screen_width = self.root.winfo_screenwidth()
        self.label = tk.Label(self.root, text="", font=("Arial", FONT_BOYUTU, "bold"), fg=FONT_RENGI, bg=ARKA_PLAN_RENGI, wraplength=self.screen_width * 0.8, justify="center", padx=15, pady=10); self.label.pack()
    def update_text(self, text):
        if not text: self.root.geometry('1x1+-10+-10'); return
        self.label.config(text=text); self.root.update_idletasks()
        width = self.label.winfo_reqwidth(); height = self.label.winfo_reqheight()
        x = (self.screen_width // 2) - (width // 2); y = EKRAN_UST_BOSLUK
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    def run(self): self.root.mainloop()

def start_gui():
    global gui; gui = OverlayGUI(); gui.run()

def main_translation_loop():
    sct = mss.mss(); time.sleep(2)
    while True:
        if not is_paused:
            try:
                ekran_goruntusu = sct.grab(altyazi_bolgesi)
                img = np.array(ekran_goruntusu); gri_img = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
                _, islenmis_img = cv2.threshold(gri_img, 180, 255, cv2.THRESH_BINARY_INV)
                metin = pytesseract.image_to_string(islenmis_img, lang='eng')
                temiz_metin = metin.strip().replace('\n', ' ')
                global son_metin
                if temiz_metin and temiz_metin != son_metin:
                    son_metin = temiz_metin
                    try: cevirilmis = translator.translate_text(temiz_metin, source_lang="EN", target_lang="TR");
                    except Exception as e: print(f"!! ÇEVİRİ HATASI: {e}"); cevirilmis = None
                    if gui and cevirilmis: gui.update_text(cevirilmis.text)
                elif not temiz_metin and son_metin: son_metin = ""; gui.update_text("")
            except Exception as e: print(f"ANA DÖNGÜ HATASI: {e}"); son_metin = ""; gui.update_text("[Program hatası...]")
        time.sleep(KONTROL_ARALIGI)

# --- Ana Başlangıç Noktası ---
if __name__ == "__main__":
    keyboard.add_hotkey(DURDUR_DEVAM_ET_TUSU, toggle_pause)
    keyboard.add_hotkey(PROGRAMI_KAPAT_TUSU, quit_program)
    keyboard.add_hotkey(ALAN_SEC_TUSU, alani_sec_ve_kaydet) # YENİ: Kısayol ataması
    gui_thread = threading.Thread(target=start_gui, daemon=True); gui_thread.start()
    translation_thread = threading.Thread(target=main_translation_loop, daemon=True); translation_thread.start()
    image = Image.open("icon.png")
    menu = (item('Duraklat', toggle_pause), item('Altyazı Alanını Seç', alani_sec_ve_kaydet), item('Çıkış', quit_program))
    tray_icon = pystray.Icon("Oyun Çeviri", image, "Oyun Çeviri Aracı", menu); tray_icon.run()