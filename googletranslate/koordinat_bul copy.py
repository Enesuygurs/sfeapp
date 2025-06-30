import pyautogui
import time

print("Koordinat bulma aracı başladı.")
print("Fare imlecini istediğin yere getir. 5 saniye sonra pozisyon yazdırılacak.")
print("Programı durdurmak için CTRL+C'ye bas.")

try:
    while True:
        time.sleep(5)
        x, y = pyautogui.position()
        print(f"Fare Pozisyonu: x={x}  y={y}")
except KeyboardInterrupt:
    print("\nProgram durduruldu.")