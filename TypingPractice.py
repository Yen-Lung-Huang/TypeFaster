import urwid
import random
import string
import time

str_vkey_tip = "Virtual Keyboard"

class Key:
    def __init__(self, display_text, char, key_positions, highlight_color='keyboard', name=None, zhuyin_char=None):
        self.name = name if name else display_text.strip()
        self.display_text = display_text  # The text to display (English)
        self.zhuyin_char = zhuyin_char    # The Zhuyin character to display
        self.char = char                  # Associated character (English key)
        self.key_positions = key_positions  # Tuple of (row, start_col, end_col)
        self.highlight_color = highlight_color
        self.widget_text = urwid.Text(display_text, align='center')
        self.widget = urwid.AttrMap(self.widget_text, highlight_color)

    def get_widget(self):
        return self.widget

    def get_positions(self):
        return self.key_positions
    
    def set_mode(self, mode):
        if mode == 'zhuyin' and self.zhuyin_char:
            self.widget_text.set_text(self.zhuyin_char)
        else:
            self.widget_text.set_text(self.display_text)

class TypingPractice:
    special_char_mapping = {
        '~': '`', '!': '1', '@': '2', '#': '3', '$': '4',
        '%': '5', '^': '6', '&': '7', '*': '8', '(': '9',
        ')': '0', '_': '-', '+': '=', '{': '[', '}': ']',
        '|': '\\', ':': ';', '"': "'", '<': ',', '>': '.',
        '?': '/'
    }

    # Standard Zhuyin (Daqian) Layout
    zhuyin_mapping = {
        '1': 'ㄅ', 'q': 'ㄆ', 'a': 'ㄇ', 'z': 'ㄈ',
        '2': 'ㄉ', 'w': 'ㄊ', 's': 'ㄋ', 'x': 'ㄌ',
        '3': 'ˇ', 'e': 'ㄍ', 'd': 'ㄎ', 'c': 'ㄏ',
        '4': 'ˋ', 'r': 'ㄐ', 'f': 'ㄑ', 'v': 'ㄒ',
        '5': 'ㄓ', 't': 'ㄔ', 'g': 'ㄕ', 'b': 'ㄖ',
        '6': 'ˊ', 'y': 'ㄗ', 'h': 'ㄘ', 'n': 'ㄙ',
        '7': '˙', 'u': 'ㄧ', 'j': 'ㄨ', 'm': 'ㄩ',
        '8': 'ㄚ', 'i': 'ㄛ', 'k': 'ㄜ', ',': 'ㄝ',
        '9': 'ㄞ', 'o': 'ㄟ', 'l': 'ㄠ', '.': 'ㄡ',
        '0': 'ㄢ', 'p': 'ㄣ', ';': 'ㄤ', '/': 'ㄥ',
        '-': 'ㄦ'
    }

    def __init__(self):
        self.show_keyboard = True
        self.mode = 'english' # 'english' or 'zhuyin'
        self.current_char = self._generate_random_char()
        self.correct_count = 0
        self.total_count = 0

        # Define key position mappings
        self.key_positions = {
            '⇧ (L)': (3, 0, 3),    # Left Shift
            '⇧ (R)': (3, 25, 27),  # Right Shift
            '⭾': (1, 0, 1),        # Tab
            '↲': (2, 26, 27),      # Enter
            '⇪': (2, 0, 2),        # Caps Lock
            '⇦': (0, 26, 27),      # Backspace
            "―       ―": (4, 9, 17) # Space bar
        }

        self.txt_target = urwid.Text([('bold', "Target Character: "), ('bold_target', f" {self.current_char} ")], align='center')
        self.txt_stats = urwid.Text(('bold', "Accuracy: 0% (0/0)"), align='center')
        self.txt_instruction = urwid.Text(('instruction', "Press ESC to exit | F1 to toggle Mode"), align='center')
        self.txt_mode = urwid.Text(('bold', f"Mode: {self.mode.capitalize()}"), align='center')

        self.toggle_button_text = urwid.SelectableIcon(('bold', f"▼ {str_vkey_tip}"), 0, align='center')
        self.toggle_button = urwid.Button('')
        self.toggle_button._w = self.toggle_button_text
        urwid.connect_signal(self.toggle_button, 'click', self.toggle_keyboard)
        self.toggle_button = urwid.AttrMap(self.toggle_button, 'toggle_button')

        self.key_coordinates = {}
        self.keys_objects = {} # Store Key objects to update them later
        self.keyboard_padding = self._create_keyboard_padding()

        self.pile = urwid.Pile([
            urwid.Divider(),
            self.txt_mode,
            urwid.Divider(),
            self.txt_target,
            urwid.Divider(),
            self.txt_stats,
            urwid.Divider(),
            self.txt_instruction,
            urwid.Divider(),
            urwid.Padding(self.toggle_button, width=25, align='center'),
            urwid.Divider(),
            self.keyboard_padding
        ])

        padded_pile = urwid.Padding(self.pile, align='center', width=('relative', 90))
        self.main_widget = urwid.Filler(padded_pile, 'middle')

        self.loop = urwid.MainLoop(
            self.main_widget,
            palette=[
                ('bold', 'white,bold', 'default'),
                ('bold_target', 'white,bold', 'dark gray'),
                ('bold_correct', 'white,bold', 'dark green'),
                ('bold_wrong', 'white,bold', 'dark red'),
                ('bold_correct_text', 'dark green,bold', 'default'),
                ('bold_wrong_text', 'dark red,bold', 'default'),
                ('keyboard', 'white', 'default'),
                ('key_highlight', 'black,bold', 'yellow'),
                ('key_default', 'default,bold', 'dark gray'),
                ('key_pressed', 'white,bold', 'light cyan'),
                ('key_correct', 'black', 'dark green'),
                ('key_wrong', 'black', 'dark red'),
                ('toggle_button', 'default,bold', 'default'),
                ('instruction', 'dark gray,bold', 'default'),
            ],
            unhandled_input=self.handle_input
        )

        # List of special keys that should remain highlighted
        self.persistent_highlight_keys = ['⇧', '⭾', '↲', '⇪', '⇦', "―       ―"]
        self._highlight_persistent_keys()

        # Define left hand keys (standard touch typing)
        self.left_hand_keys = set([
            '`', '1', '2', '3', '4', '5',
            'Q', 'W', 'E', 'R', 'T',
            'A', 'S', 'D', 'F', 'G',
            'Z', 'X', 'C', 'V', 'B'
        ])

    def _create_keyboard_padding(self):
        self.keyboard_layout = self._create_keyboard_layout()
        self.keyboard_widget = urwid.AttrMap(self.keyboard_layout, 'keyboard')
        self.keyboard_box = urwid.LineBox(self.keyboard_widget)

        max_width = max([sum(len(col[0].base_widget.text) for col in row[0].contents) for row in self.keyboard_layout.contents]) + 2

        return urwid.Padding(
            self.keyboard_box,
            align='center',
            width=max_width,
            min_width=40,
            left=1,
            right=1
        )

    def toggle_keyboard(self, button):
        if self.show_keyboard:
            self.pile.contents = [c for c in self.pile.contents if c[0] != self.keyboard_padding]
            self.toggle_button_text.set_text(('bold', f"▶ {str_vkey_tip}"))
        else:
            self.keyboard_padding = self._create_keyboard_padding()
            self.pile.contents.insert(-1, (self.keyboard_padding, ('pack', None)))
            self.toggle_button_text.set_text(('bold', f"▼ {str_vkey_tip}"))

        self.show_keyboard = not self.show_keyboard
        if self.show_keyboard:
            self._reset_keyboard_highlight()
            self._highlight_key(self.current_char)

    def _create_keyboard_layout(self):
        keyboard_rows = [
            "` 1 2 3 4 5 6 7 8 9 0 - = ⇦",
            " ⭾ Q W E R T Y U I O P [ ] \\",
            "  ⇪ A S D F G H J K L ; ' ↲",
            "   ⇧ Z X C V B N M , . / ⇧",
            "         ―       ―"
        ]

        keyboard_widgets = []
        for row_idx, row in enumerate(keyboard_rows):
            row_buttons = []
            col_idx = 0
            while col_idx < len(row):
                key = row[col_idx]

                # Handle special keys with specific positions
                if key == '⇧' and col_idx < 4:  # Left Shift
                    key_obj = Key("⇧", 'shift_left', self.key_positions['⇧ (L)'], highlight_color='key_default')
                    self.key_coordinates['⇧ (L)'] = (row_idx, len(row_buttons))
                    row_buttons.append(('pack', key_obj.get_widget()))
                elif key == '⇧' and col_idx > 20:  # Right Shift
                    key_obj = Key("⇧", 'shift_right', self.key_positions['⇧ (R)'], highlight_color='key_default')
                    self.key_coordinates['⇧ (R)'] = (row_idx, len(row_buttons))
                    row_buttons.append(('pack', key_obj.get_widget()))
                elif row[col_idx:col_idx + 9] == "―       ―":  # Space bar
                    key_obj = Key("―       ―", " ", self.key_positions["―       ―"], highlight_color='key_default')
                    self.key_coordinates["―       ―"] = (row_idx, len(row_buttons))
                    row_buttons.append(('pack', key_obj.get_widget()))
                    col_idx += 8
                else:
                    key_positions = (row_idx, col_idx, col_idx)
                    zhuyin = self.zhuyin_mapping.get(key.lower())
                    key_obj = Key(key, key, key_positions, zhuyin_char=zhuyin)
                    self.key_coordinates[key] = (row_idx, len(row_buttons))
                    self.keys_objects[key] = key_obj # Store for mode switching
                    row_buttons.append(('pack', key_obj.get_widget()))

                col_idx += 1
            
            row_widget = urwid.Columns(row_buttons, dividechars=0)
            keyboard_widgets.append(row_widget)

        return urwid.Pile(keyboard_widgets)

    def _generate_random_char(self):
        if self.mode == 'english':
            # Use both ascii_letters (contains lower and upper case) along with digits and punctuation.
            chars = string.ascii_letters + string.digits + string.punctuation
            return random.choice(chars)
        else: # Zhuyin mode
            return random.choice(list(self.zhuyin_mapping.values()))

    def _highlight_key(self, char):
        # Store the original character before any mapping.
        original_char = char
        
        # Find the key to highlight
        key_to_highlight = None
        
        if self.mode == 'english':
            # If the character requires a special mapping (e.g., '!' maps to '1'),
            # then use the mapped value.
            if char in self.special_char_mapping:
                char = self.special_char_mapping[char]
            # Convert the character to uppercase for key coordinate lookup.
            key_to_highlight = char.upper()
        else: # Zhuyin mode
            # Find the key that corresponds to the Zhuyin char
            for k, v in self.zhuyin_mapping.items():
                if v == char:
                    key_to_highlight = k.upper()
                    break
        
        if not key_to_highlight:
            return

        # Highlight the target key if it exists on the keyboard.
        if key_to_highlight in self.key_coordinates:
            row_idx, col_idx = self.key_coordinates[key_to_highlight]
            
            display_text = key_to_highlight
            if self.mode == 'zhuyin' and key_to_highlight.lower() in self.zhuyin_mapping:
                 display_text = self.zhuyin_mapping[key_to_highlight.lower()]

            self.keyboard_layout.contents[row_idx][0].contents[col_idx] = (
                urwid.AttrMap(urwid.Text(display_text, align='center'), 'key_highlight'),
                ('pack', None, False)
            )
        
        # Only highlight Shift keys if the original character requires Shift (English mode only mostly)
        if self.mode == 'english':
            if (original_char.isalpha() and original_char.isupper()) or (original_char in self.special_char_mapping):
                # Determine which Shift key to use
                # If the key is typed with the left hand, use Right Shift.
                # If the key is typed with the right hand, use Left Shift.
                
                shift_key_to_use = "⇧ (L)" # Default to Left Shift (for right hand keys)
                if key_to_highlight in self.left_hand_keys:
                    shift_key_to_use = "⇧ (R)"
                
                if shift_key_to_use in self.key_coordinates:
                    shift_row, shift_col = self.key_coordinates[shift_key_to_use]
                    self.keyboard_layout.contents[shift_row][0].contents[shift_col] = (
                        urwid.AttrMap(urwid.Text("⇧", align='center'), 'key_highlight'),
                        ('pack', None, False)
                    )

    def _highlight_persistent_keys(self):
        for key in self.persistent_highlight_keys:
            if key in self.key_coordinates:
                row_idx, col_idx = self.key_coordinates[key]
                self.keyboard_layout.contents[row_idx][0].contents[col_idx] = (
                    urwid.AttrMap(urwid.Text(key, align='center'), 'key_default'),
                    ('pack', None, False)
                )

    def _reset_keyboard_highlight(self, loop=None, user_data=None):
        # Store the original target character.
        original_target = self.current_char
        
        # Determine target key and shift requirement
        target_key = None
        shift_required = False
        
        if self.mode == 'english':
            if original_target in self.special_char_mapping:
                target_key = self.special_char_mapping[original_target]
                shift_required = True
            else:
                target_key = original_target.upper() if original_target.isalpha() else original_target
                if original_target.isalpha() and original_target.isupper():
                    shift_required = True
        else: # Zhuyin
             for k, v in self.zhuyin_mapping.items():
                if v == original_target:
                    target_key = k.upper()
                    break

        target_coords = self.key_coordinates.get(target_key, None)

        # Iterate over each row in the keyboard layout.
        for row_idx, row in enumerate(self.keyboard_layout.contents):
            row_widget = row[0]
            # Iterate over each key in the current row.
            for col_idx, (col, _) in enumerate(row_widget.contents):
                key_char = col.base_widget.get_text()[0]
                
                # We need to find the original key char to check against target_coords
                # This is a bit tricky because the display text might be Zhuyin now.
                # Let's rely on coordinates.
                
                is_target = (row_idx, col_idx) == target_coords
                
                if not is_target:
                     # Reconstruct the default widget for this position
                     # We need to find which key this is.
                     found_key = None
                     for k, coords in self.key_coordinates.items():
                         if coords == (row_idx, col_idx):
                             found_key = k
                             break
                     
                     if found_key:
                         display_text = found_key
                         if self.mode == 'zhuyin' and found_key.lower() in self.zhuyin_mapping:
                             display_text = self.zhuyin_mapping[found_key.lower()]
                         elif found_key in self.persistent_highlight_keys:
                             display_text = found_key

                         style = 'keyboard'
                         if found_key in self.persistent_highlight_keys:
                             style = 'key_default'

                         self.keyboard_layout.contents[row_idx][0].contents[col_idx] = (
                            urwid.AttrMap(urwid.Text(display_text, align='center'), style),
                            ('pack', None, False)
                        )

        # Reset Shift keys
        for shift_key in ["⇧ (L)", "⇧ (R)"]:
            if shift_key in self.key_coordinates:
                shift_row, shift_col = self.key_coordinates[shift_key]
                self.keyboard_layout.contents[shift_row][0].contents[shift_col] = (
                    urwid.AttrMap(urwid.Text("⇧", align='center'), 'key_default'),
                    ('pack', None, False)
                )
        
        if shift_required and self.mode == 'english':
            shift_key_to_use = "⇧ (L)" # Default
            if target_key in self.left_hand_keys:
                shift_key_to_use = "⇧ (R)"
            
            if shift_key_to_use in self.key_coordinates:
                shift_row, shift_col = self.key_coordinates[shift_key_to_use]
                self.keyboard_layout.contents[shift_row][0].contents[shift_col] = (
                    urwid.AttrMap(urwid.Text("⇧", align='center'), 'key_highlight'),
                    ('pack', None, False)
                )

    def toggle_mode(self):
        self.mode = 'zhuyin' if self.mode == 'english' else 'english'
        self.txt_mode.set_text(('bold', f"Mode: {self.mode.capitalize()}"))
        
        # Update keyboard labels
        for key_char, key_obj in self.keys_objects.items():
            key_obj.set_mode(self.mode)
            # We need to refresh the layout with new text
            # But since we are reconstructing the layout in _reset_keyboard_highlight mostly,
            # we just need to trigger a reset/redraw.
            
        self.current_char = self._generate_random_char()
        self.txt_target.set_text([('bold', "Target Character: "), ('bold_target', f" {self.current_char} ")])
        self.correct_count = 0
        self.total_count = 0
        self.txt_stats.set_text(('bold', "Accuracy: 0% (0/0)"))
        
        if self.show_keyboard:
            self._reset_keyboard_highlight()
            self._highlight_key(self.current_char)
            
        self.loop.draw_screen()

    def handle_input(self, key):
        if key == 'esc':
            raise urwid.ExitMainLoop()
        
        if key == 'f1':
            self.toggle_mode()
            return

        if key == 'tab':
            self.toggle_keyboard(None)
            return

        if isinstance(key, str) and len(key) == 1:
            self.total_count += 1
            if self.show_keyboard:
                self._reset_keyboard_highlight()

            key_upper = key.upper()
            
            # Determine mapped key for highlighting
            mapped_key = key_upper
            if self.mode == 'english':
                mapped_key = self.special_char_mapping.get(key_upper, key_upper)
            
            # Check correctness
            is_correct = False
            if self.mode == 'english':
                if key == self.current_char:
                    is_correct = True
            else: # Zhuyin
                # Check if the pressed key corresponds to the target Zhuyin char
                if key.lower() in self.zhuyin_mapping and self.zhuyin_mapping[key.lower()] == self.current_char:
                    is_correct = True
            
            # Visual feedback on keyboard
            target_key_for_highlight = mapped_key # Default
            if self.mode == 'zhuyin':
                 # If we pressed '1', mapped_key is '1'. 
                 # If target was 'ㄅ', and we pressed '1', it's correct.
                 pass

            if mapped_key in self.key_coordinates:
                row_idx, col_idx = self.key_coordinates[mapped_key]
                
                display_text = mapped_key
                if self.mode == 'zhuyin' and mapped_key.lower() in self.zhuyin_mapping:
                    display_text = self.zhuyin_mapping[mapped_key.lower()]

                if is_correct:
                    self.keyboard_layout.contents[row_idx][0].contents[col_idx] = (
                        urwid.AttrMap(urwid.Text(display_text, align='center'), 'key_correct'),
                        ('pack', None, False)
                    )
                else:
                    self.keyboard_layout.contents[row_idx][0].contents[col_idx] = (
                        urwid.AttrMap(urwid.Text(display_text, align='center'), 'key_wrong'),
                        ('pack', None, False)
                    )

            if is_correct:
                self.correct_count += 1
                self.txt_target.set_text([('bold', "Target Character: "), ('bold_correct', f" {self.current_char} "), ('bold_correct_text', " ✓ Correct")])
                self.loop.draw_screen()
                time.sleep(0.1) # Reduced sleep for faster typing
                self.current_char = self._generate_random_char()
                self.txt_target.set_text([('bold', "Target Character: "), ('bold_target', f" {self.current_char} ")])
            else:
                self.txt_target.set_text([('bold', "Target Character: "), ('bold_wrong', f" {self.current_char} "), ('bold_wrong_text', " ✗ Wrong")])
                self.loop.draw_screen()
                time.sleep(0.1)
                self.txt_target.set_text([('bold', "Target Character: "), ('bold_target', f" {self.current_char} ")])

            accuracy = (self.correct_count / self.total_count) * 100
            self.txt_stats.set_text(('bold', f"Accuracy: {accuracy:.1f}% ({self.correct_count}/{self.total_count})"))

            if self.show_keyboard:
                self._highlight_key(self.current_char)

            self.loop.set_alarm_in(0.2, self._reset_keyboard_highlight)

        elif key in ['shift', 'enter', ' ']:
            if self.show_keyboard:
                self._reset_keyboard_highlight()

            # Handle special keys visual feedback
            if key in self.key_coordinates:
                row_idx, col_idx = self.key_coordinates[key]
                self.keyboard_layout.contents[row_idx][0].contents[col_idx] = (
                    urwid.AttrMap(urwid.Text(key.capitalize(), align='center'), 'key_default'),
                    ('pack', None, False)
                )

            self.loop.draw_screen()
            self.loop.set_alarm_in(0.2, self._reset_keyboard_highlight)

    def run(self):
        if self.show_keyboard:
            self._highlight_key(self.current_char)
        self.loop.run()

if __name__ == '__main__':
    app = TypingPractice()
    app.run()