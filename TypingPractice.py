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
    
    def set_style(self, style):
        self.highlight_color = style
        self.widget.set_attr_map({None: style})

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
        self.modes = ['english', 'zhuyin', 'mixed']
        self.mode = 'english'
        
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

        # Finger Mappings (Updated Colors)
        # Thumb: Purple (Dark Magenta)
        # Pinky: Red
        # Ring: Yellow
        # Middle: Green
        # Index: Blue
        self.finger_mapping = {}
        
        # Pinky (Red)
        for k in ['`', '1', 'Q', 'A', 'Z', '0', '-', '=', 'P', '[', ']', '\\', ';', "'", '/', '⇧', '⭾', '↲', '⇪', '⇦']:
            self.finger_mapping[k] = 'pinky'
        
        # Ring (Yellow)
        for k in ['2', 'W', 'S', 'X', '9', 'O', 'L', '.']:
            self.finger_mapping[k] = 'ring'
            
        # Middle (Green)
        for k in ['3', 'E', 'D', 'C', '8', 'I', 'K', ',']:
            self.finger_mapping[k] = 'middle'
            
        # Index (Blue)
        for k in ['4', '5', 'R', 'T', 'F', 'G', 'V', 'B', '6', '7', 'Y', 'U', 'H', 'J', 'N', 'M']:
            self.finger_mapping[k] = 'index'
            
        # Thumb (Purple)
        self.finger_mapping["―       ―"] = 'thumb'
        self.finger_mapping[" "] = 'thumb'

        self.txt_target = urwid.Text([('bold', "Target Character: "), ('bold_target', f" {self.current_char} ")], align='center')
        self.txt_stats = urwid.Text(('bold', "Accuracy: 0% (0/0)"), align='center')
        self.txt_instruction = urwid.Text(('instruction', "Press ESC to exit"), align='center')
        
        # Graphical Mode Buttons
        self.mode_buttons = []
        self.mode_buttons_widgets = []
        for m in self.modes:
            # Create a button with a custom label
            btn = urwid.Button("")
            # We use a SelectableIcon as the button widget to have full control over text
            icon = urwid.SelectableIcon(self._get_mode_label(m), 0)
            btn._w = urwid.AttrMap(icon, 'mode_button', 'mode_button_focus')
            urwid.connect_signal(btn, 'click', self.on_mode_click, m)
            self.mode_buttons.append(btn)
            self.mode_buttons_widgets.append(('pack', btn))
            
        self.mode_columns = urwid.Columns(self.mode_buttons_widgets, dividechars=2)
        self.mode_container = urwid.Padding(self.mode_columns, align='center', width='pack')

        self.toggle_button_text = urwid.SelectableIcon(('bold', f"▼ {str_vkey_tip}"), 0, align='center')
        self.toggle_button = urwid.Button('')
        self.toggle_button._w = self.toggle_button_text
        urwid.connect_signal(self.toggle_button, 'click', self.toggle_keyboard)
        self.toggle_button = urwid.AttrMap(self.toggle_button, 'toggle_button', 'toggle_button')

        self.key_coordinates = {}
        self.keys_objects = {} # Store Key objects to update them later
        self.keyboard_padding = self._create_keyboard_padding()

        self.pile = urwid.Pile([
            urwid.Divider(),
            self.mode_container,
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
                ('bold_target', 'yellow,bold', 'dark blue'),
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
                ('mode_button', 'default,bold', 'default'),
                ('mode_button_focus', 'default,bold', 'default'), 
                ('instruction', 'dark gray,bold', 'default'),
                
                # Finger Colors (Updated)
                # Pinky: Red
                ('key_pinky', 'light red,bold', 'default'),
                ('highlight_pinky', 'black,bold', 'light red'),
                
                # Ring: Yellow
                ('key_ring', 'yellow,bold', 'default'),
                ('highlight_ring', 'black,bold', 'yellow'),
                
                # Middle: Green
                ('key_middle', 'light green,bold', 'default'),
                ('highlight_middle', 'black,bold', 'light green'),
                
                # Index: Blue
                ('key_index', 'light blue,bold', 'default'),
                ('highlight_index', 'black,bold', 'light blue'),
                
                # Thumb: Purple
                ('key_thumb', 'dark magenta,bold', 'default'),
                ('highlight_thumb', 'black,bold', 'dark magenta'),
            ],
            unhandled_input=self.handle_input
        )

        # List of special keys that should remain highlighted (but now they have finger colors)
        self.persistent_highlight_keys = ['⇧', '⭾', '↲', '⇪', '⇦', "―       ―"]
        
        # Define left hand keys (standard touch typing)
        self.left_hand_keys = set([
            '`', '1', '2', '3', '4', '5',
            'Q', 'W', 'E', 'R', 'T',
            'A', 'S', 'D', 'F', 'G',
            'Z', 'X', 'C', 'V', 'B'
        ])

    def _get_mode_label(self, mode):
        icon = "■" if self.mode == mode else "□"
        return f"{icon} {mode.capitalize()}"

    def on_mode_click(self, button, mode):
        self.set_mode(mode)

    def set_mode(self, mode):
        if self.mode == mode:
            return # Already in this mode
            
        self.mode = mode
        
        # Update all button labels
        for i, m in enumerate(self.modes):
            # Access the SelectableIcon inside the AttrMap inside the Button
            # btn._w is AttrMap, btn._w.base_widget is SelectableIcon
            self.mode_buttons[i]._w.base_widget.set_text(self._get_mode_label(m))
            
        # Update keyboard labels
        for key_char, key_obj in self.keys_objects.items():
            key_obj.set_mode(self.mode)
        
        # Recreate keyboard padding to adjust width
        if self.show_keyboard:
            self.pile.contents = [c for c in self.pile.contents if c[0] != self.keyboard_padding]
            self.keyboard_padding = self._create_keyboard_padding()
            self.pile.contents.insert(-1, (self.keyboard_padding, ('pack', None)))
            
        self.current_char = self._generate_random_char()
        self.txt_target.set_text([('bold', "Target Character: "), ('bold_target', f" {self.current_char} ")])
        self.correct_count = 0
        self.total_count = 0
        self.txt_stats.set_text(('bold', "Accuracy: 0% (0/0)"))
        
        if self.show_keyboard:
            self._reset_keyboard_highlight()
            self._highlight_key(self.current_char)
            
        self.loop.draw_screen()

    def _get_key_style(self, key_char, highlight=False):
        finger = self.finger_mapping.get(key_char.upper(), 'keyboard')
        if finger == 'keyboard':
             return 'key_highlight' if highlight else 'keyboard'
        
        if highlight:
            return f'highlight_{finger}'
        else:
            return f'key_{finger}'

    def _create_keyboard_padding(self):
        self.keyboard_layout = self._create_keyboard_layout()
        self.keyboard_widget = urwid.AttrMap(self.keyboard_layout, 'keyboard')
        self.keyboard_box = urwid.LineBox(self.keyboard_widget)

        max_row_width = 0
        for row in self.keyboard_layout.contents:
            row_widget = row[0] # Columns
            current_row_width = 0
            for col, options in row_widget.contents:
                text_widget = col.base_widget
                text = text_widget.text
                w = 0
                for char in text:
                    if ord(char) > 127: w += 2
                    else: w += 1
                current_row_width += w
            max_row_width = max(max_row_width, current_row_width)
            
        return urwid.Padding(
            self.keyboard_box,
            align='center',
            width=max_row_width + 2,
            min_width=40,
            left=0,
            right=0
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

                if key == '⇧' and col_idx < 4:  # Left Shift
                    style = self._get_key_style('⇧')
                    key_obj = Key("⇧", 'shift_left', self.key_positions['⇧ (L)'], highlight_color=style)
                    self.key_coordinates['⇧ (L)'] = (row_idx, len(row_buttons))
                    row_buttons.append(('pack', key_obj.get_widget()))
                elif key == '⇧' and col_idx > 15:  # Right Shift
                    style = self._get_key_style('⇧')
                    key_obj = Key("⇧", 'shift_right', self.key_positions['⇧ (R)'], highlight_color=style)
                    self.key_coordinates['⇧ (R)'] = (row_idx, len(row_buttons))
                    row_buttons.append(('pack', key_obj.get_widget()))
                elif row[col_idx:col_idx + 9] == "―       ―":  # Space bar
                    style = self._get_key_style("―       ―")
                    key_obj = Key("―       ―", " ", self.key_positions["―       ―"], highlight_color=style)
                    self.key_coordinates["―       ―"] = (row_idx, len(row_buttons))
                    row_buttons.append(('pack', key_obj.get_widget()))
                    col_idx += 8
                elif key == ' ':
                    row_buttons.append(('pack', urwid.Text(' ')))
                else:
                    key_positions = (row_idx, col_idx, col_idx)
                    zhuyin = self.zhuyin_mapping.get(key.lower())
                    style = self._get_key_style(key)
                    key_obj = Key(key, key, key_positions, highlight_color=style, zhuyin_char=zhuyin)
                    self.key_coordinates[key] = (row_idx, len(row_buttons))
                    self.keys_objects[key] = key_obj
                    row_buttons.append(('pack', key_obj.get_widget()))

                col_idx += 1
            
            row_widget = urwid.Columns(row_buttons, dividechars=0)
            keyboard_widgets.append(row_widget)

        return urwid.Pile(keyboard_widgets)

    def _generate_random_char(self):
        target_mode = self.mode
        if self.mode == 'mixed':
            target_mode = random.choice(['english', 'zhuyin'])
            
        if target_mode == 'english':
            chars = string.ascii_letters + string.digits + string.punctuation
            return random.choice(chars)
        else: # Zhuyin mode
            return random.choice(list(self.zhuyin_mapping.values()))

    def _highlight_key(self, char):
        original_char = char
        
        current_char_mode = 'english'
        if char in self.zhuyin_mapping.values():
            current_char_mode = 'zhuyin'
        
        key_to_highlight = None
        
        if current_char_mode == 'english':
            if char in self.special_char_mapping:
                char = self.special_char_mapping[char]
            key_to_highlight = char.upper()
        else: # Zhuyin mode
            for k, v in self.zhuyin_mapping.items():
                if v == char:
                    key_to_highlight = k.upper()
                    break
        
        if not key_to_highlight:
            return

        if key_to_highlight in self.key_coordinates:
            row_idx, col_idx = self.key_coordinates[key_to_highlight]
            
            display_text = key_to_highlight
            
            if self.mode == 'mixed':
                 # In mixed mode, if it's a Zhuyin target, show Zhuyin on the key?
                 # Or keep English?
                 # Let's show Zhuyin if target is Zhuyin to help user.
                 if current_char_mode == 'zhuyin' and key_to_highlight.lower() in self.zhuyin_mapping:
                     display_text = self.zhuyin_mapping[key_to_highlight.lower()]
                 else:
                     display_text = key_to_highlight
            elif self.mode == 'zhuyin' and key_to_highlight.lower() in self.zhuyin_mapping:
                 display_text = self.zhuyin_mapping[key_to_highlight.lower()]

            style = self._get_key_style(key_to_highlight, highlight=True)

            self.keyboard_layout.contents[row_idx][0].contents[col_idx] = (
                urwid.AttrMap(urwid.Text(display_text, align='center'), style),
                ('pack', None, False)
            )
        
        if current_char_mode == 'english':
            if (original_char.isalpha() and original_char.isupper()) or (original_char in self.special_char_mapping):
                shift_key_to_use = "⇧ (L)"
                if key_to_highlight in self.left_hand_keys:
                    shift_key_to_use = "⇧ (R)"
                
                if shift_key_to_use in self.key_coordinates:
                    shift_row, shift_col = self.key_coordinates[shift_key_to_use]
                    style = self._get_key_style('⇧', highlight=True)
                    self.keyboard_layout.contents[shift_row][0].contents[shift_col] = (
                        urwid.AttrMap(urwid.Text("⇧", align='center'), style),
                        ('pack', None, False)
                    )

    def _reset_keyboard_highlight(self, loop=None, user_data=None):
        original_target = self.current_char
        
        current_char_mode = 'english'
        if original_target in self.zhuyin_mapping.values():
            current_char_mode = 'zhuyin'
            
        target_key = None
        shift_required = False
        
        if current_char_mode == 'english':
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

        for row_idx, row in enumerate(self.keyboard_layout.contents):
            row_widget = row[0]
            for col_idx, (col, _) in enumerate(row_widget.contents):
                found_key = None
                for k, coords in self.key_coordinates.items():
                    if coords == (row_idx, col_idx):
                        found_key = k
                        break
                
                if found_key:
                    display_text = found_key
                    
                    if self.mode == 'zhuyin' and found_key.lower() in self.zhuyin_mapping:
                        display_text = self.zhuyin_mapping[found_key.lower()]
                    elif self.mode == 'mixed':
                        # Reset to English for consistency when not highlighted
                        pass
                    
                    lookup_key = found_key
                    if '⇧' in found_key:
                        lookup_key = '⇧'
                    
                    style = self._get_key_style(lookup_key, highlight=False)

                    self.keyboard_layout.contents[row_idx][0].contents[col_idx] = (
                    urwid.AttrMap(urwid.Text(display_text, align='center'), style),
                    ('pack', None, False)
                )

        for shift_key in ["⇧ (L)", "⇧ (R)"]:
            if shift_key in self.key_coordinates:
                shift_row, shift_col = self.key_coordinates[shift_key]
                style = self._get_key_style('⇧', highlight=False)
                self.keyboard_layout.contents[shift_row][0].contents[shift_col] = (
                    urwid.AttrMap(urwid.Text("⇧", align='center'), style),
                    ('pack', None, False)
                )
        
        if shift_required and current_char_mode == 'english':
            shift_key_to_use = "⇧ (L)"
            if target_key in self.left_hand_keys:
                shift_key_to_use = "⇧ (R)"
            
            if shift_key_to_use in self.key_coordinates:
                shift_row, shift_col = self.key_coordinates[shift_key_to_use]
                style = self._get_key_style('⇧', highlight=True)
                self.keyboard_layout.contents[shift_row][0].contents[shift_col] = (
                    urwid.AttrMap(urwid.Text("⇧", align='center'), style),
                    ('pack', None, False)
                )

    def handle_input(self, key):
        if key == 'esc':
            raise urwid.ExitMainLoop()
        
        if key == 'tab':
            self.toggle_keyboard(None)
            return

        if isinstance(key, str) and len(key) == 1:
            self.total_count += 1
            if self.show_keyboard:
                self._reset_keyboard_highlight()

            key_upper = key.upper()
            
            mapped_key = key_upper
            if self.mode == 'english':
                mapped_key = self.special_char_mapping.get(key_upper, key_upper)
            elif self.mode == 'mixed':
                mapped_key = self.special_char_mapping.get(key_upper, key_upper)
            
            is_correct = False
            
            current_char_mode = 'english'
            if self.current_char in self.zhuyin_mapping.values():
                current_char_mode = 'zhuyin'
                
            if current_char_mode == 'english':
                if key == self.current_char:
                    is_correct = True
            else: # Zhuyin
                if key.lower() in self.zhuyin_mapping and self.zhuyin_mapping[key.lower()] == self.current_char:
                    is_correct = True
            
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
                time.sleep(0.1)
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
        try:
            self.loop.run()
        except KeyboardInterrupt:
            pass

if __name__ == '__main__':
    app = TypingPractice()
    app.run()