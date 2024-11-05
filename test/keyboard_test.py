import keyboard

def on_key_event(e):
    if e.event_type == 'down':
        if e.name == 'tab':
            print("Tab key pressed")
        elif e.scan_code == 42:
            print("Left Shift key pressed")
        elif e.scan_code == 54:
            print("Right Shift key pressed")
        elif e.name == 'enter':
            print("Enter key pressed")
        elif e.name == 'space':
            print("Space key pressed")
        elif e.name == 'caps lock':
            print("Caps Lock key pressed")
        elif e.name == 'backspace':
            print("Backspace key pressed")

# 設定監聽鍵盤事件
keyboard.hook(on_key_event)

print("Press ESC to stop...")
keyboard.wait('esc')  # 按 ESC 鍵停止程式
