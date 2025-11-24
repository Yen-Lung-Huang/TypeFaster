import urwid
from TypingPractice import TypingPractice
import time

# Mock MainLoop to avoid running the full UI loop
class MockLoop:
    def draw_screen(self): pass
    def set_alarm_in(self, sec, callback): pass

def test_crash():
    app = TypingPractice()
    app.loop = MockLoop()
    
    print("Initial mode:", app.mode)
    
    print("Switching to Zhuyin...")
    app.set_mode('zhuyin')
    print("Mode is now:", app.mode)
    
    print("Switching to English...")
    app.set_mode('english')
    print("Mode is now:", app.mode)
    print("Current char:", app.current_char)

if __name__ == "__main__":
    try:
        test_crash()
        print("Test finished successfully.")
    except Exception as e:
        print("Test failed with exception:")
        print(e)
