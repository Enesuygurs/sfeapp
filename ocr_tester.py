import cv2
import numpy as np
import mss
from config_manager import AYARLAR

class OCRTespitAraci:
    def __init__(self, bolge):
        self.bolge = bolge
        self.window_name = "OCR Canli Onizleme"
        self.controls_window_name = "Kontrol Paneli"

    def run(self):
        cv2.namedWindow(self.window_name)
        cv2.namedWindow(self.controls_window_name)

        mod_map = {"gri_esik": 0, "adaptif_esik": 1, "renk_filtresi": 2}
        initial_mode = mod_map.get(AYARLAR['isleme_modu'], 0)

        cv2.createTrackbar("Mod (0:Gri 1:Adaptif 2:Renk)", self.controls_window_name, initial_mode, 2, lambda x: None)
        cv2.createTrackbar("Gri Esik Degeri", self.controls_window_name, AYARLAR['esik_degeri'], 255, lambda x: None)
        cv2.createTrackbar("H Min", self.controls_window_name, AYARLAR['renk_alt_sinir_h'], 179, lambda x: None)
        cv2.createTrackbar("S Min", self.controls_window_name, AYARLAR['renk_alt_sinir_s'], 255, lambda x: None)
        cv2.createTrackbar("V Min", self.controls_window_name, AYARLAR['renk_alt_sinir_v'], 255, lambda x: None)
        cv2.createTrackbar("H Max", self.controls_window_name, AYARLAR['renk_ust_sinir_h'], 179, lambda x: None)
        cv2.createTrackbar("S Max", self.controls_window_name, AYARLAR['renk_ust_sinir_s'], 255, lambda x: None)
        cv2.createTrackbar("V Max", self.controls_window_name, AYARLAR['renk_ust_sinir_v'], 255, lambda x: None)

        print("Onizleme baslatildi. Kapatmak icin 'q' tusuna basin veya pencereyi kapatin.")

        with mss.mss() as sct:
            while True:
                # Pencerenin kullanıcı tarafından kapatılıp kapatılmadığını kontrol et
                # Bu, getTrackbarPos'tan önce yapılmalı
                if cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) < 1 or cv2.getWindowProperty(self.controls_window_name, cv2.WND_PROP_VISIBLE) < 1:
                    break

                img = np.array(sct.grab(self.bolge))
                
                mode = cv2.getTrackbarPos("Mod (0:Gri 1:Adaptif 2:Renk)", self.controls_window_name)
                threshold_val = cv2.getTrackbarPos("Gri Esik Degeri", self.controls_window_name)
                h_min = cv2.getTrackbarPos("H Min", self.controls_window_name)
                s_min = cv2.getTrackbarPos("S Min", self.controls_window_name)
                v_min = cv2.getTrackbarPos("V Min", self.controls_window_name)
                h_max = cv2.getTrackbarPos("H Max", self.controls_window_name)
                s_max = cv2.getTrackbarPos("S Max", self.controls_window_name)
                v_max = cv2.getTrackbarPos("V Max", self.controls_window_name)

                if mode == 2:
                    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                    hsv_img = cv2.cvtColor(hsv_img, cv2.COLOR_BGR2HSV)
                    lower_bound = np.array([h_min, s_min, v_min])
                    upper_bound = np.array([h_max, s_max, v_max])
                    islenmis_img = cv2.inRange(hsv_img, lower_bound, upper_bound)
                else:
                    gri_img = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
                    if mode == 1:
                        islenmis_img = cv2.adaptiveThreshold(gri_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
                    else:
                        _, islenmis_img = cv2.threshold(gri_img, threshold_val, 255, cv2.THRESH_BINARY)
                
                islenmis_img_bgr = cv2.cvtColor(islenmis_img, cv2.COLOR_GRAY2BGR)
                orijinal_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                combined_view = np.hstack((orijinal_bgr, islenmis_img_bgr))
                
                cv2.imshow(self.window_name, combined_view)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        # --- DEĞİŞİKLİK BURADA: Neşter (Hedefli Temizlik) Kullanımı ---
        cv2.destroyWindow(self.window_name)
        cv2.destroyWindow(self.controls_window_name)
        # --- BİTİŞ ---

        print("Onizleme kapatildi.")