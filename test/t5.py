import urwid
import random
import string
import time

class Key:
    def __init__(self, display_text, char, key_positions, highlight_color='keyboard', name=None):
        self.name = name if name else display_text.strip()
        self.display_text = display_text  # The text to display
        self.char = char                  # Associated character
        self.key_positions = key_positions  # Tuple of (row, start_col, end_col)
        self.highlight_color = highlight_color
        self.widget = urwid.AttrMap(urwid.Text(display_text, align='center'), highlight_color)

    def get_widget(self):
        return self.widget

    def get_positions(self):
        return self.key_positions

class TypingPractice:
    special_char_mapping = {
        '~': '`', '!': '1', '@': '2', '#': '3', '$': '4',
        '%': '5', '^': '6', '&': '7', '*': '8', '(': '9',
        ')': '0', '_': '-', '+': '=', '{': '[', '}': ']',
        '|': '\\', ':': ';', '"': "'", '<': ',', '>': '.',
        '?': '/'
    }

    def __init__(self):
        self.show_keyboard = True
        self.current_char = self._generate_random_char()
        self.correct_count = 0
        self.total_count = 0

        # Define key position mappings
        self.key_positions = {
            '⇧ (L)': (3, 0, 3),    # Left Shift
            '⇧ (R)': (3, 25, 27),  # Right Shift
            '⭾': (1, 1, 2),        # Tab
            '↲': (2, 23, 24),      # Enter
            '⇪': (2, 2, 3),        # Caps Lock
            '⇦': (0, 26, 27),      # Backspace
            "―       ―": (4, 9, 17) # Space bar
        }

        self.txt_target = urwid.Text([('bold', "Target Character: "), ('bold_target', f" {self.current_char} ")], align='center')
        self.txt_stats = urwid.Text(('bold', "Accuracy: 0% (0/0)"), align='center')
        self.txt_instruction = urwid.Text(('instruction', "Press ESC to exit"), align='center')

        self.toggle_button_text = urwid.SelectableIcon(('bold', "▼ Toggle Virtual Keyboard"), 0)
        self.toggle_button = urwid.Button('')
        self.toggle_button._w = self.toggle_button_text
        urwid.connect_signal(self.toggle_button, 'click', self.toggle_keyboard)
        self.toggle_button = urwid.AttrMap(self.toggle_button, 'toggle_button')

        self.key_coordinates = {}
        self.keyboard_padding = self._create_keyboard_padding()

        self.pile = urwid.Pile([
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
                ('keyboard', 'white', 'black'),
                ('key_highlight', 'black', 'yellow'),
                ('key_pressed', 'black', 'light cyan'),
                ('key_correct', 'black', 'dark green'),
                ('key_wrong', 'black', 'dark red'),
                ('toggle_button', 'black,bold', 'dark gray'),
                ('instruction', 'dark gray,bold', 'default'),
            ],
            unhandled_input=self.handle_input
        )

        # List of special keys that should remain highlighted
        self.persistent_highlight_keys = ['⇧', '⭾', '↲', '⇪', '⇦', "―       ―"]
        self._highlight_persistent_keys()

    # Rest of the methods remain the same as in your original code...
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
            self.toggle_button_text.set_text(('bold', "▶ Toggle Virtual Keyboard"))
        else:
            self.keyboard_padding = self._create_keyboard_padding()
            self.pile.contents.insert(-1, (self.keyboard_padding, ('pack', None)))
            self.toggle_button_text.set_text(('bold', "▼ Toggle Virtual Keyboard"))

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
                    key_obj = Key("⇧", 'shift_left', self.key_positions['⇧ (L)'], highlight_color='key_pressed')
                    self.key_coordinates['⇧ (L)'] = (row_idx, len(row_buttons))
                    row_buttons.append(('pack', key_obj.get_widget()))
                elif key == '⇧' and col_idx > 20:  # Right Shift
                    key_obj = Key("⇧", 'shift_right', self.key_positions['⇧ (R)'], highlight_color='key_pressed')
                    self.key_coordinates['⇧ (R)'] = (row_idx, len(row_buttons))
                    row_buttons.append(('pack', key_obj.get_widget()))
                elif row[col_idx:col_idx + 9] == "―       ―":  # Space bar
                    key_obj = Key("―       ―", " ", self.key_positions["―       ―"], highlight_color='key_pressed')
                    self.key_coordinates["―       ―"] = (row_idx, len(row_buttons))
                    row_buttons.append(('pack', key_obj.get_widget()))
                    col_idx += 8
                else:
                    key_positions = (row_idx, col_idx, col_idx)
                    key_obj = Key(key, key, key_positions)
                    self.key_coordinates[key] = (row_idx, len(row_buttons))
                    row_buttons.append(('pack', key_obj.get_widget()))

                col_idx += 1
            
            row_widget = urwid.Columns(row_buttons, dividechars=0)
            keyboard_widgets.append(row_widget)

        return urwid.Pile(keyboard_widgets)

    # Include all other methods from your original code...
    def _generate_random_char(self):
        chars = string.ascii_uppercase + string.digits + string.punctuation
        return random.choice(chars)

    def _highlight_key(self, char):
        if char in self.special_char_mapping:
            char = self.special_char_mapping[char]
        char = char.upper()
        if char in self.key_coordinates:
            row_idx, col_idx = self.key_coordinates[char]
            self.keyboard_layout.contents[row_idx][0].contents[col_idx] = (
                urwid.AttrMap(urwid.Text(char, align='center'), 'key_highlight'),
                ('pack', None, False)
            )

    def _highlight_persistent_keys(self):
        for key in self.persistent_highlight_keys:
            if key in self.key_coordinates:
                row_idx, col_idx = self.key_coordinates[key]
                self.keyboard_layout.contents[row_idx][0].contents[col_idx] = (
                    urwid.AttrMap(urwid.Text(key, align='center'), 'key_pressed'),
                    ('pack', None, False)
                )

    def _reset_keyboard_highlight(self, loop=None, user_data=None):
        target_char = self.current_char.upper()
        target_coords = None

        if target_char in self.special_char_mapping:
            target_char = self.special_char_mapping[target_char]
        if target_char in self.key_coordinates:
            target_coords = self.key_coordinates[target_char]

        for row_idx, row in enumerate(self.keyboard_layout.contents):
            row_widget = row[0]
            for col_idx, (col, _) in enumerate(row_widget.contents):
                key = col.base_widget.get_text()[0]
                if key.strip() and (row_idx, col_idx) != target_coords:
                    # Below line is modified to skip resetting the Shift keys
                    if key not in ['⇧', '⇧']:  # or use an identifier for shift keys if you have those
                        self.keyboard_layout.contents[row_idx][0].contents[col_idx] = (
                            urwid.AttrMap(urwid.Text(key, align='center'), 'keyboard'),
                            ('pack', None, False)
                        )

        self._highlight_persistent_keys()

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
            mapped_key = self.special_char_mapping.get(key_upper, key_upper)
            if mapped_key in self.key_coordinates:
                row_idx, col_idx = self.key_coordinates[mapped_key]
                if key == self.current_char:
                    self.keyboard_layout.contents[row_idx][0].contents[col_idx] = (
                        urwid.AttrMap(urwid.Text(mapped_key, align='center'), 'key_correct'),
                        ('pack', None, False)
                    )
                else:
                    self.keyboard_layout.contents[row_idx][0].contents[col_idx] = (
                        urwid.AttrMap(urwid.Text(mapped_key, align='center'), 'key_wrong'),
                        ('pack', None, False)
                    )

            if key == self.current_char:
                self.correct_count += 1
                self.txt_target.set_text([('bold', "Target Character: "), ('bold_correct', f" {self.current_char} "), ('bold_correct_text', " Correct")])
                self.loop.draw_screen()
                time.sleep(0.5)
                self.current_char = self._generate_random_char()
                self.txt_target.set_text([('bold', "Target Character: "), ('bold_target', f" {self.current_char} ")])
            else:
                self.txt_target.set_text([('bold', "Target Character: "), ('bold_wrong', f" {self.current_char} "), ('bold_wrong_text', " Wrong")])
                self.loop.draw_screen()
                time.sleep(0.5)
                self.txt_target.set_text([('bold', "Target Character: "), ('bold_target', f" {self.current_char} ")])

            accuracy = (self.correct_count / self.total_count) * 100
            self.txt_stats.set_text(('bold', f"Accuracy: {accuracy:.1f}% ({self.correct_count}/{self.total_count})"))

            if self.show_keyboard:
                self._highlight_key(self.current_char)

            self.loop.set_alarm_in(0.5, self._reset_keyboard_highlight)

        elif key in ['shift', 'enter', ' ']:
            if self.show_keyboard:
                self._reset_keyboard_highlight()

            # 特別處理 Shift 鍵
            if key in self.key_coordinates:
                row_idx, col_idx = self.key_coordinates[key]
                self.keyboard_layout.contents[row_idx][0].contents[col_idx] = (
                    urwid.AttrMap(urwid.Text(key.capitalize(), align='center'), 'key_pressed'),
                    ('pack', None, False)
                )

            self.loop.draw_screen()
            self.loop.set_alarm_in(0.5, self._reset_keyboard_highlight)

    def run(self):
        if self.show_keyboard:
            self._highlight_key(self.current_char)
        self.loop.run()

if __name__ == '__main__':
    app = TypingPractice()
    app.run()