import urwid
import random
import string
import time

class Key:
    def __init__(self, display_text, char, row, start_col, end_col, highlight_color='keyboard', name=None):
        self.name = name if name else display_text.strip()
        self.display_text = display_text  # 顯示的字串，例如"―       ―"
        self.char = char                    # 關聯的字符，例如' '
        self.row = row                      # 在鍵盤中的行
        self.start_col = start_col          # 起始列
        self.end_col = end_col              # 結束列（若僅占一列，可與 start_col 相同）
        self.highlight_color = highlight_color  # 預設顏色（例如 'keyboard' 或 'key_pressed'）
        self.widget = urwid.AttrMap(urwid.Text(display_text, align='center'), highlight_color)

    def set_highlight(self, highlight_color):
        self.widget = urwid.AttrMap(urwid.Text(self.display_text, align='center'), highlight_color)

    def get_widget(self):
        return self.widget

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
                ('instruction', 'dark gray,bold', 'default')
            ],
            unhandled_input=self.handle_input
        )

        # Persistent keys list, including both Shift keys and the "Space" placeholder
        self.persistent_highlight_keys = ['⇧', '⭾', '↲', '⇪', '⇦', "―       ―"]
        self._highlight_persistent_keys()

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
            "         ―       ―    "
        ]

        keyboard_widgets = []
        for row_idx, row in enumerate(keyboard_rows):
            row_buttons = []
            col_idx = 0
            while col_idx < len(row):
                key = row[col_idx]

                if key == ' ':
                    key_obj = Key(' ', ' ', row_idx, col_idx, col_idx)
                    row_buttons.append(('pack', key_obj.get_widget()))
                elif row[col_idx:col_idx+9] == "―       ―":  # Detect and handle the full "Space" key
                    key_obj = Key("―       ―", " ", row_idx, col_idx, col_idx + 8)
                    self.key_coordinates["―       ―"] = (row_idx, len(row_buttons))  # Add "Space" key to coordinates
                    row_buttons.append(('pack', key_obj.get_widget()))
                    col_idx += 8  # Skip over the full length of "―       ―"
                else:
                    key_obj = Key(key, key, row_idx, col_idx, col_idx)
                    self.key_coordinates[key] = (row_idx, len(row_buttons))
                    row_buttons.append(('pack', key_obj.get_widget()))

                col_idx += 1

            row_widget = urwid.Columns(row_buttons, dividechars=0)
            keyboard_widgets.append(row_widget)

        return urwid.Pile(keyboard_widgets)

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
