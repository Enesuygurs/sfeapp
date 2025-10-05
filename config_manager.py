import os
import sys
import json
import configparser

CONFIG_FILE = 'config.ini'
SETTINGS = {}
LANG_STRINGS = {}
SUPPORTED_INTERFACE_LANGUAGES = {}
SUPPORTED_TARGET_LANGUAGES = {}
config = configparser.ConfigParser()

def get_lang(key, **kwargs):
    return LANG_STRINGS.get(key, key).format(**kwargs)

def get_key_from_value(dictionary, value):
    return next((k for k, v in dictionary.items() if v == value), None)

def get_resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except Exception: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_interface_language(lang_code):
    global LANG_STRINGS
    try:
        lang_file_path = get_resource_path(f"lang/{lang_code.lower()}.json")
        with open(lang_file_path, 'r', encoding='utf-8') as f: LANG_STRINGS = json.load(f)
    except FileNotFoundError:
        lang_file_path = get_resource_path("lang/en.json")
        with open(lang_file_path, 'r', encoding='utf-8') as f: LANG_STRINGS = json.load(f)

def save_settings():
    config['Genel'] = {'tesseract_yolu': SETTINGS['tesseract_yolu'], 'api_anahtari': SETTINGS['api_anahtari'], 'arayuz_dili': SETTINGS['arayuz_dili'], 'hedef_dil': SETTINGS['hedef_dil'], 'baslangicta_baslat': str(SETTINGS['baslangicta_baslat'])}
    config['Bolge'] = {'top': str(SETTINGS['top']), 'left': str(SETTINGS['left']), 'width': str(SETTINGS['width']), 'height': str(SETTINGS['height'])}
    config['OCR'] = {'isleme_modu': SETTINGS['isleme_modu'], 'esik_degeri': str(SETTINGS['esik_degeri']), 'otomatik_ters_cevirme': str(SETTINGS['otomatik_ters_cevirme']), 'otomatik_ters_cevirme_esigi': str(SETTINGS['otomatik_ters_cevirme_esigi']), 'renk_alt_sinir_h': str(SETTINGS['renk_alt_sinir_h']), 'renk_alt_sinir_s': str(SETTINGS['renk_alt_sinir_s']), 'renk_alt_sinir_v': str(SETTINGS['renk_alt_sinir_v']), 'renk_ust_sinir_h': str(SETTINGS['renk_ust_sinir_h']), 'renk_ust_sinir_s': str(SETTINGS['renk_ust_sinir_s']), 'renk_ust_sinir_v': str(SETTINGS['renk_ust_sinir_v'])}
    config['Arayuz'] = {
        'font_ailesi': SETTINGS['font_ailesi'], 'font_boyutu': str(SETTINGS['font_boyutu']),
        'font_kalin': str(SETTINGS['font_kalin']), 'font_italik': str(SETTINGS['font_italik']), 'font_alti_cizili': str(SETTINGS['font_alti_cizili']),
        'font_rengi': SETTINGS['font_rengi'], 'arka_plan_rengi': SETTINGS['arka_plan_rengi'], 'seffaflik': str(SETTINGS['seffaflik']),
        'ekran_ust_bosluk': str(SETTINGS['ekran_ust_bosluk']), 'kontrol_araligi': str(SETTINGS['kontrol_araligi']),
        'ceviri_omru': str(SETTINGS['ceviri_omru']), 'kaynak_metin_benzerlik_esigi': str(SETTINGS['kaynak_metin_benzerlik_esigi']),
        'kaynak_metin_min_uzunluk': str(SETTINGS['kaynak_metin_min_uzunluk'])
    }
    config['Kisayollar'] = {'alan_sec': SETTINGS['alan_sec'], 'durdur_devam_et': SETTINGS['durdur_devam_et'], 'programi_kapat': SETTINGS['programi_kapat']}
    with open(CONFIG_FILE, 'w', encoding='utf-8') as configfile: config.write(configfile)

def load_settings():
    global SUPPORTED_TARGET_LANGUAGES, SUPPORTED_INTERFACE_LANGUAGES, SETTINGS
    with open(get_resource_path('diller.json'), 'r', encoding='utf-8') as f: SUPPORTED_TARGET_LANGUAGES = json.load(f)
    with open(get_resource_path('arayuz_dilleri.json'), 'r', encoding='utf-8') as f: SUPPORTED_INTERFACE_LANGUAGES = json.load(f)
    if not os.path.exists(CONFIG_FILE):
        config['Genel'] = {'tesseract_yolu': '', 'api_anahtari': '', 'arayuz_dili': 'TR', 'hedef_dil': 'TR', 'baslangicta_baslat': 'True'}
        config['Bolge'] = {'top': '0', 'left': '0', 'width': '0', 'height': '0'}
        config['OCR'] = {'isleme_modu': 'renk_filtresi', 'esik_degeri': '180', 'otomatik_ters_cevirme': 'True', 'otomatik_ters_cevirme_esigi': '127', 'renk_alt_sinir_h': '0', 'renk_alt_sinir_s': '0', 'renk_alt_sinir_v': '180', 'renk_ust_sinir_h': '180', 'renk_ust_sinir_s': '30', 'renk_ust_sinir_v': '255'}
        config['Arayuz'] = {
            'font_ailesi': 'Arial', 'font_boyutu': '20', 'font_kalin': 'True', 'font_italik': 'False', 'font_alti_cizili': 'False',
            'font_rengi': 'white', 'arka_plan_rengi': 'black', 'seffaflik': '0.7',
            'ekran_ust_bosluk': '30', 'kontrol_araligi': '0.4', 'ceviri_omru': '3.0',
            'kaynak_metin_benzerlik_esigi': '0.9', 'kaynak_metin_min_uzunluk': '3'
        }
        config['Kisayollar'] = {'alan_sec': 'f8', 'durdur_devam_et': 'f9', 'programi_kapat': 'f10'}
        with open(CONFIG_DOSYASI, 'w', encoding='utf-8') as configfile: config.write(configfile)
    config.read(CONFIG_FILE, encoding='utf-8')
    SETTINGS = {
        'tesseract_yolu': config.get('Genel', 'tesseract_yolu', fallback=''), 'api_anahtari': config.get('Genel', 'api_anahtari', fallback=''),
        'baslangicta_baslat': config.getboolean('Genel', 'baslangicta_baslat', fallback=True), 'arayuz_dili': config.get('Genel', 'arayuz_dili', fallback='TR'),
        'hedef_dil': config.get('Genel', 'hedef_dil', fallback='TR'),
        'top': config.getint('Bolge', 'top', fallback=0), 'left': config.getint('Bolge', 'left', fallback=0), 'width': config.getint('Bolge', 'width', fallback=0), 'height': config.getint('Bolge', 'height', fallback=0),
        'isleme_modu': config.get('OCR', 'isleme_modu', fallback='gri_esik'), 'esik_degeri': config.getint('OCR', 'esik_degeri', fallback=180),
        'otomatik_ters_cevirme': config.getboolean('OCR', 'otomatik_ters_cevirme', fallback=True), 'otomatik_ters_cevirme_esigi': config.getint('OCR', 'otomatik_ters_cevirme_esigi', fallback=127),
        'renk_alt_sinir_h': config.getint('OCR', 'renk_alt_sinir_h', fallback=0), 'renk_alt_sinir_s': config.getint('OCR', 'renk_alt_sinir_s', fallback=0), 'renk_alt_sinir_v': config.getint('OCR', 'renk_alt_sinir_v', fallback=180),
        'renk_ust_sinir_h': config.getint('OCR', 'renk_ust_sinir_h', fallback=180), 'renk_ust_sinir_s': config.getint('OCR', 'renk_ust_sinir_s', fallback=30), 'renk_ust_sinir_v': config.getint('OCR', 'renk_ust_sinir_v', fallback=255),
        'font_ailesi': config.get('Arayuz', 'font_ailesi', fallback='Arial'),
        'font_boyutu': config.getint('Arayuz', 'font_boyutu', fallback=20),
        'font_kalin': config.getboolean('Arayuz', 'font_kalin', fallback=True),
        'font_italik': config.getboolean('Arayuz', 'font_italik', fallback=False),
        'font_alti_cizili': config.getboolean('Arayuz', 'font_alti_cizili', fallback=False),
        'font_rengi': config.get('Arayuz', 'font_rengi', fallback='white'), 'arka_plan_rengi': config.get('Arayuz', 'arka_plan_rengi', fallback='black'),
        'seffaflik': config.getfloat('Arayuz', 'seffaflik', fallback=0.7), 'ekran_ust_bosluk': config.getint('Arayuz', 'ekran_ust_bosluk', fallback=30), 'kontrol_araligi': config.getfloat('Arayuz', 'kontrol_araligi', fallback=0.4),
        'ceviri_omru': config.getfloat('Arayuz', 'ceviri_omru', fallback=3.0), 'kaynak_metin_benzerlik_esigi': config.getfloat('Arayuz', 'kaynak_metin_benzerlik_esigi', fallback=0.9), 'kaynak_metin_min_uzunluk': config.getint('Arayuz', 'kaynak_metin_min_uzunluk', fallback=3),
        'alan_sec': config.get('Kisayollar', 'alan_sec', fallback='f8'), 'durdur_devam_et': config.get('Kisayollar', 'durdur_devam_et', fallback='f9'), 'programi_kapat': config.get('Kisayollar', 'programi_kapat', fallback='f10')
    }
    load_interface_language(SETTINGS['arayuz_dili'])

load_settings()