import pyautogui

def is_capslock_on():
    # If Caps Lock is on, this will return 'Caps Lock: On'
    caps_lock_status = pyautogui.getWindowsWithTitle("Caps Lock: On")
    return bool(caps_lock_status)

if __name__ == "__main__":
    if is_capslock_on():
        print("Caps Lock is ON")
    else:
        print("Caps Lock is OFF")
