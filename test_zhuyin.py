import unittest
import string
from unittest.mock import MagicMock
from TypingPractice import TypingPractice

class TestTypingPractice(unittest.TestCase):
    def setUp(self):
        self.app = TypingPractice()
        # Mock the loop to prevent draw_screen from failing
        self.app.loop = MagicMock()

    def test_english_mode_default(self):
        self.assertEqual(self.app.mode, 'english')
        self.assertTrue(self.app.current_char in string.ascii_letters + string.digits + string.punctuation)

    def test_zhuyin_mapping(self):
        # Test a few mappings
        self.assertEqual(self.app.zhuyin_mapping['1'], 'ㄅ')
        self.assertEqual(self.app.zhuyin_mapping['q'], 'ㄆ')
        self.assertEqual(self.app.zhuyin_mapping['-'], 'ㄦ')

    def test_mode_switching(self):
        self.app.toggle_mode()
        self.assertEqual(self.app.mode, 'zhuyin')
        # Check if current_char is a Zhuyin character
        self.assertTrue(self.app.current_char in self.app.zhuyin_mapping.values())
        
        self.app.toggle_mode()
        self.assertEqual(self.app.mode, 'english')

    def test_highlight_key_logic(self):
        # Test English highlight logic
        self.app.mode = 'english'
        self.app._highlight_key('a')
        
        # Test Zhuyin highlight logic
        self.app.mode = 'zhuyin'
        self.app._highlight_key('ㄅ') # Should highlight '1'

    def test_smart_shift_highlighting(self):
        self.app.mode = 'english'
        
        # Test Left Hand Key -> Right Shift should highlight
        # 'A' is a left hand key
        self.app._highlight_key('A')
        # We can't inspect the UI widget easily, but we can check if it runs
        # and maybe check internal state if we exposed it, but for now just running it ensures no crash
        
        # Test Right Hand Key -> Left Shift should highlight
        # 'J' is a right hand key
        self.app._highlight_key('J')
        
if __name__ == '__main__':
    unittest.main()
