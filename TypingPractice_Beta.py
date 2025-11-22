import urwid
import random
import string
import time

class KeyboardState:
    def __init__(self):
        self.is_visible = True
        self.toggle_text = "▼ Virtual Keyboard"
    
    def toggle(self):
        self.is_visible = not self.is_visible
        self.toggle_text = "▼ Virtual Keyboard" if self.is_visible else "▶ Virtual Keyboard"
        return self.is_visible

class Key:
    def __init__(self, display_text, char, key_positions, highlight_color='keyboard', name=None):
        self.name = name if name else display_text.strip()
        self.display_text = display_text
        self.char = char
        self.key_positions = key_positions
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
        self.keyboard_state = KeyboardState()
        self.current_char = self._generate_random_char()
        self.correct_count = 0
        self.total_count = 0

        self.key_positions = {
            '⇧ (L)': (3, 0, 3),
            '⇧ (R)': (3, 25, 27),
            '⭾': (1, 0, 1),
            '↲': (2, 26, 27),
            '⇪': (2, 0, 2),
            '⇦': (0, 26, 27),
            "―       ―": (4, 9, 17)
        }

        self.txt_target = urwid.Text([('bold', "Target Character: "), ('bold_target', f" {self.current_char} ")], align='center')
        self.txt_stats = urwid.Text(('bold', "Accuracy: 0% (0/0)"), align='center')
        self.txt_instruction = urwid.Text(('instruction', "Press ESC to exit"), align='center')

        self.toggle_button_text = urwid.SelectableIcon(('bold', self.keyboard_state.toggle_text), 0, align='center')
        self.toggle_button = urwid.Button('')
        self.toggle_button._w = self.toggle_button_text
        urwid.connect_signal(self.toggle_button, 'click', self.toggle_keyboard)
        self.toggle_button = urwid.AttrMap(self.toggle_button, 'toggle_button')

        self.key_coordinates = {}
        self.keyboard_padding = self._create_keyboard_padding()
        
        # Initialize pile contents based on keyboard state
        pile_contents = [
            urwid.Divider(),
            self.txt_target,
            urwid.Divider(),
            self.txt_stats,
            urwid.Divider(),
            self.txt_instruction,
            urwid.Divider(),
            urwid.Padding(self.toggle_button, width=25, align='center')
        ]
        
        if self.keyboard_state.is_visible:
            pile_contents.append(self.keyboard_padding)

        self.pile = urwid.Pile(pile_contents)
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
            unhandled_input=self.handle_input,
            handle_mouse=False  # Disable mouse handling
        )

        self.persistent_highlight_keys = ['⇧', '⭾', '↲', '⇪', '⇦', "―       ―"]
        self._highlight_persistent_keys()

    def toggle_keyboard(self, button):
        is_visible = self.keyboard_state.toggle()
        if not is_visible:
            self.pile.contents = [c for c in self.pile.contents if c[0] != self.keyboard_padding]
        else:
            self.keyboard_padding = self._create_keyboard_padding()
            self.pile.contents.append((self.keyboard_padding, ('pack', None)))
        
        self.toggle_button_text.set_text(('bold', self.keyboard_state.toggle_text))
        
        if is_visible:
            self._reset_keyboard_highlight()
            self._highlight_key(self.current_char)

    def handle_input(self, key):
        if key == 'esc':
            self.loop.screen.stop()  # Stop the screen before exiting
            raise urwid.ExitMainLoop()

        # Rest of the handle_input method remains the same...
        if key == 'tab':
            self.toggle_keyboard(None)
            return

        if isinstance(key, str) and len(key) == 1:
            self.total_count += 1
            if self.keyboard_state.is_visible:
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
                self.txt_target.set_text([('bold', "Target Character: "), ('bold_correct', f" {self.current_char} "), ('bold_correct_text', " ✓ Correct")])
                self.loop.draw_screen()
                time.sleep(0.5)
                self.current_char = self._generate_random_char()
                self.txt_target.set_text([('bold', "Target Character: "), ('bold_target', f" {self.current_char} ")])
            else:
                self.txt_target.set_text([('bold', "Target Character: "), ('bold_wrong', f" {self.current_char} "), ('bold_wrong_text', " ✗ Wrong")])
                self.loop.draw_screen()
                time.sleep(0.5)
                self.txt_target.set_text([('bold', "Target Character: "), ('bold_target', f" {self.current_char} ")])

            accuracy = (self.correct_count / self.total_count) * 100
            self.txt_stats.set_text(('bold', f"Accuracy: {accuracy:.1f}% ({self.correct_count}/{self.total_count})"))

            if self.keyboard_state.is_visible:
                self._highlight_key(self.current_char)

            self.loop.set_alarm_in(0.5, self._reset_keyboard_highlight)

    # Other methods remain the same...

if __name__ == '__main__':
    app = TypingPractice()
    app.run()