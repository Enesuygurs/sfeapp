import os
import sys
import json
import configparser

CONFIG_DOSYASI = 'config.ini'
AYARLAR = {}
LANG_STRINGS = {}
DESTEKLENEN_ARAYUZ_DILLERI = {}
DESTEKLENEN_HEDEF_DILLER = {}
config = configparser.ConfigParser()

def get_lang(key, **kwargs):
    return LANG_STRINGS.get(key, key).format(**kwargs)

def get_key_from_value(dictionary, value):
    return next((k for k, v in dictionary.items() if v == value), None)

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def arayuz_dilini_yukle(dil_kodu):
    global LANG_STRINGS
    try:
        lang_file_path = get_resource_path(f"lang/{dil_kodu.lower()}.json")
        with open(lang_file_path, 'r', encoding='utf-8') as f:
            LANG_STRINGS = json.load(f)
    except FileNotFoundError:
        lang_file_path = get_resource_path("lang/en.json")
        with open(lang_file_path, 'r', encoding='utf-8') as f:
            LANG_STRINGS = json.load(f)

def ayarlari_kaydet():
    config['Genel'] = {'tesseract_yolu': AYARLAR['tesseract_yolu'], 'api_anahtari': AYARLAR['api_anahtari'], 'arayuz_dili': AYARLAR['arayuz_dili'], 'hedef_dil': AYARLAR['hedef_dil'], 'baslangicta_baslat': str(AYARLAR['baslangicta_baslat'])}
    config['Bolge'] = {'top': str(AYARLAR['top']), 'left': str(AYARLAR['left']), 'width': str(AYARLAR['width']), 'height': str(AYARLAR['height'])}
    config['OCR'] = {'isleme_modu': AYARLAR['isleme_modu'], 'esik_degeri': str(AYARLAR['esik_degeri']), 'renk_alt_sinir_h': str(AYARLAR['renk_alt_sinir_h']), 'renk_alt_sinir_s': str(AYARLAR['renk_alt_sinir_s']), 'renk_alt_sinir_v': str(AYARLAR['renk_alt_sinir_v']), 'renk_ust_sinir_h': str(AYARLAR['renk_ust_sinir_h']), 'renk_ust_sinir_s': str(AYARLAR['renk_ust_sinir_s']), 'renk_ust_sinir_v': str(AYARLAR['renk_ust_sinir_v'])}
    config['Arayuz'] = {'font_boyutu': str(AYARLAR['font_boyutu']), 'font_rengi': AYARLAR['font_rengi'], 'arka_plan_rengi': AYARLAR['arka_plan_rengi'], 'seffaflik': str(AYARLAR['seffaflik']), 'ekran_ust_bosluk': str(AYARLAR['ekran_ust_bosluk']), 'kontrol_araligi': str(AYARLAR['kontrol_araligi']), 'ceviri_omru': str(AYARLAR['ceviri_omru']), 'benzerlik_orani_esigi': str(AYARLAR['benzerlik_orani_esigi'])}
    config['Kisayollar'] = {'alan_sec': AYARLAR['alan_sec'], 'durdur_devam_et': AYARLAR['durdur_devam_et'], 'programi_kapat': AYARLAR['programi_kapat']}
    with open(CONFIG_DOSYASI, 'w', encoding='utf-8') as configfile:
        config.write(configfile)

def ayarlari_yukle():
    global DESTEKLENEN_HEDEF_DILLER, DESTEKLENEN_ARAYUZ_DILLERI, AYARLAR
    with open(get_resource_path('diller.json'), 'r', encoding='utf-8') as f:
        DESTEKLENEN_HEDEF_DILLER = json.load(f)
    with open(get_resource_path('arayuz_dilleri.json'), 'r', encoding='utf-8') as f:
        DESTEKLENEN_ARAYUZ_DILLERI = json.load(f)
    if not os.path.exists(CONFIG_DOSYASI):
        config['Genel'] = {'tesseract_yolu': '', 'api_anahtari': '', 'arayuz_dili': 'TR', 'hedef_dil': 'TR', 'baslangicta_baslat': 'True'}
        config['Bolge'] = {'top': '0', 'left': '0', 'width': '0', 'height': '0'}
        config['OCR'] = {'isleme_modu': 'renk', 'esik_degeri': '180', 'renk_alt_sinir_h': '0', 'renk_alt_sinir_s': '0', 'renk_alt_sinir_v': '180', 'renk_ust_sinir_h': '180', 'renk_ust_sinir_s': '30', 'renk_ust_sinir_v': '255'}
        config['Arayuz'] = {'font_boyutu': '20', 'font_rengi': 'white', 'arka_plan_rengi': 'black', 'seffaflik': '0.7', 'ekran_ust_bosluk': '30', 'kontrol_araligi': '0.4', 'ceviri_omru': '3.0', 'benzerlik_orani_esigi': '0.85'}
        config['Kisayollar'] = {'alan_sec': 'f8', 'durdur_devam_et': 'f9', 'programi_kapat': 'f10'}
        with open(CONFIG_DOSYASI, 'w', encoding='utf-8') as configfile:
            config.write(configfile)
    config.read(CONFIG_DOSYASI, encoding='utf-8')
    AYARLAR = {
        'tesseract_yolu': config.get('Genel', 'tesseract_yolu', fallback=''), 'api_anahtari': config.get('Genel', 'api_anahtari', fallback=''),
        'baslangicta_baslat': config.getboolean('Genel', 'baslangicta_baslat', fallback=True), 'arayuz_dili': config.get('Genel', 'arayuz_dili', fallback='TR'),
        'hedef_dil': config.get('Genel', 'hedef_dil', fallback='TR'),
        'top': config.getint('Bolge', 'top', fallback=0), 'left': config.getint('Bolge', 'left', fallback=0),
        'width': config.getint('Bolge', 'width', fallback=0), 'height': config.getint('Bolge', 'height', fallback=0),
        'isleme_modu': config.get('OCR', 'isleme_modu', fallback='renk'), 'esik_degeri': config.getint('OCR', 'esik_degeri', fallback=180),
        'renk_alt_sinir_h': config.getint('OCR', 'renk_alt_sinir_h', fallback=0), 'renk_alt_sinir_s': config.getint('OCR', 'renk_alt_sinir_s', fallback=0),
        'renk_alt_sinir_v': config.getint('OCR', 'renk_alt_sinir_v', fallback=180), 'renk_ust_sinir_h': config.getint('OCR', 'renk_ust_sinir_h', fallback=180),
        'renk_ust_sinir_s': config.getint('OCR', 'renk_ust_sinir_s', fallback=30), 'renk_ust_sinir_v': config.getint('OCR', 'renk_ust_sinir_v', fallback=255),
        'font_boyutu': config.getint('Arayuz', 'font_boyutu', fallback=20), 'font_rengi': config.get('Arayuz', 'font_rengi', fallback='white'),
        'arka_plan_rengi': config.get('Arayuz', 'arka_plan_rengi', fallback='black'), 'seffaflik': config.getfloat('Arayuz', 'seffaflik', fallback=0.7),
        'ekran_ust_bosluk': config.getint('Arayuz', 'ekran_ust_bosluk', fallback=30), 'kontrol_araligi': config.getfloat('Arayuz', 'kontrol_araligi', fallback=0.4),
        'ceviri_omru': config.getfloat('Arayuz', 'ceviri_omru', fallback=3.0), 'benzerlik_orani_esigi': config.getfloat('Arayuz', 'benzerlik_orani_esigi', fallback=0.85),
        'alan_sec': config.get('Kisayollar', 'alan_sec', fallback='f8'), 'durdur_devam_et': config.get('Kisayollar', 'durdur_devam_et', fallback='f9'),
        'programi_kapat': config.get('Kisayollar', 'programi_kapat', fallback='f10')
    }
    arayuz_dilini_yukle(AYARLAR['arayuz_dili'])

ayarlari_yukle()