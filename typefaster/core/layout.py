from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

MODES = ("english", "zhuyin", "mixed")
LABEL_MODES = ("default", "english", "zhuyin")

Hand = Literal["left", "right", "both"]
Finger = Literal["pinky", "ring", "middle", "index", "thumb"]

HAND_LABELS = {
    "left": "Left hand",
    "right": "Right hand",
    "both": "Both thumbs",
}

FINGER_LABELS = {
    "pinky": "Pinky",
    "ring": "Ring finger",
    "middle": "Middle finger",
    "index": "Index finger",
    "thumb": "Thumb",
}

ZHUYIN_MAPPING = {
    "1": "ㄅ",
    "q": "ㄆ",
    "a": "ㄇ",
    "z": "ㄈ",
    "2": "ㄉ",
    "w": "ㄊ",
    "s": "ㄋ",
    "x": "ㄌ",
    "3": "ˇ",
    "e": "ㄍ",
    "d": "ㄎ",
    "c": "ㄏ",
    "4": "ˋ",
    "r": "ㄐ",
    "f": "ㄑ",
    "v": "ㄒ",
    "5": "ㄓ",
    "t": "ㄔ",
    "g": "ㄕ",
    "b": "ㄖ",
    "6": "ˊ",
    "y": "ㄗ",
    "h": "ㄘ",
    "n": "ㄙ",
    "7": "˙",
    "u": "ㄧ",
    "j": "ㄨ",
    "m": "ㄩ",
    "8": "ㄚ",
    "i": "ㄛ",
    "k": "ㄜ",
    ",": "ㄝ",
    "9": "ㄞ",
    "o": "ㄟ",
    "l": "ㄠ",
    ".": "ㄡ",
    "0": "ㄢ",
    "p": "ㄣ",
    ";": "ㄤ",
    "/": "ㄥ",
    "-": "ㄦ",
}

SHIFT_CHAR_MAPPING = {
    "~": "`",
    "!": "1",
    "@": "2",
    "#": "3",
    "$": "4",
    "%": "5",
    "^": "6",
    "&": "7",
    "*": "8",
    "(": "9",
    ")": "0",
    "_": "-",
    "+": "=",
    "{": "[",
    "}": "]",
    "|": "\\",
    ":": ";",
    '"': "'",
    "<": ",",
    ">": ".",
    "?": "/",
}


@dataclass(frozen=True)
class KeySpec:
    id: str
    text: str
    value: str | None
    row: int
    x: float
    width: float
    hand: Hand | None = None
    finger: Finger | None = None
    zhuyin: str | None = None
    special: bool = False


@dataclass(frozen=True)
class KeyGuide:
    target: str
    base_key_id: str
    base_key_text: str
    hand: Hand
    finger: Finger
    shift_key_id: str | None = None
    shift_hand: Hand | None = None
    shift_finger: Finger | None = None
    is_zhuyin: bool = False

    @property
    def finger_id(self) -> str:
        return f"{self.hand}_{self.finger}"

    @property
    def shift_finger_id(self) -> str | None:
        if self.shift_hand and self.shift_finger:
            return f"{self.shift_hand}_{self.shift_finger}"
        return None

    @property
    def instruction(self) -> str:
        base = f"{HAND_LABELS[self.hand]} {FINGER_LABELS[self.finger]} -> {self.base_key_text}"
        if self.shift_key_id and self.shift_hand and self.shift_finger:
            shift = f"{HAND_LABELS[self.shift_hand]} {FINGER_LABELS[self.shift_finger]} -> Shift"
            return f"{shift} + {base}"
        return base


def _key_id(value: str) -> str:
    if value == " ":
        return "space"
    names = {
        "`": "backquote",
        "-": "minus",
        "=": "equal",
        "[": "left_bracket",
        "]": "right_bracket",
        "\\": "backslash",
        ";": "semicolon",
        "'": "quote",
        ",": "comma",
        ".": "period",
        "/": "slash",
    }
    return names.get(value, value.lower())


def _append_row(specs: list[KeySpec], row: int, keys: list[tuple[str, str | None, float]]) -> None:
    x = 0.0
    for text, value, width in keys:
        if value is None:
            spec_id = text.lower().replace(" ", "_")
        else:
            spec_id = _key_id(value)
        hand, finger = FINGER_BY_KEY_ID.get(spec_id, (None, None))
        specs.append(
            KeySpec(
                id=spec_id,
                text=text,
                value=value,
                row=row,
                x=x,
                width=width,
                hand=hand,
                finger=finger,
                zhuyin=ZHUYIN_MAPPING.get(value.lower()) if value else None,
                special=value is None,
            )
        )
        x += width + 0.14


FINGER_BY_KEY_ID: dict[str, tuple[Hand, Finger]] = {
    "backquote": ("left", "pinky"),
    "1": ("left", "pinky"),
    "q": ("left", "pinky"),
    "a": ("left", "pinky"),
    "z": ("left", "pinky"),
    "tab": ("left", "pinky"),
    "caps": ("left", "pinky"),
    "left_shift": ("left", "pinky"),
    "2": ("left", "ring"),
    "w": ("left", "ring"),
    "s": ("left", "ring"),
    "x": ("left", "ring"),
    "3": ("left", "middle"),
    "e": ("left", "middle"),
    "d": ("left", "middle"),
    "c": ("left", "middle"),
    "4": ("left", "index"),
    "5": ("left", "index"),
    "r": ("left", "index"),
    "t": ("left", "index"),
    "f": ("left", "index"),
    "g": ("left", "index"),
    "v": ("left", "index"),
    "b": ("left", "index"),
    "6": ("right", "index"),
    "7": ("right", "index"),
    "y": ("right", "index"),
    "u": ("right", "index"),
    "h": ("right", "index"),
    "j": ("right", "index"),
    "n": ("right", "index"),
    "m": ("right", "index"),
    "8": ("right", "middle"),
    "i": ("right", "middle"),
    "k": ("right", "middle"),
    "comma": ("right", "middle"),
    "9": ("right", "ring"),
    "o": ("right", "ring"),
    "l": ("right", "ring"),
    "period": ("right", "ring"),
    "0": ("right", "pinky"),
    "minus": ("right", "pinky"),
    "equal": ("right", "pinky"),
    "p": ("right", "pinky"),
    "left_bracket": ("right", "pinky"),
    "right_bracket": ("right", "pinky"),
    "backslash": ("right", "pinky"),
    "semicolon": ("right", "pinky"),
    "quote": ("right", "pinky"),
    "slash": ("right", "pinky"),
    "backspace": ("right", "pinky"),
    "enter": ("right", "pinky"),
    "right_shift": ("right", "pinky"),
    "space": ("both", "thumb"),
}


@lru_cache(maxsize=1)
def get_key_specs() -> tuple[KeySpec, ...]:
    specs: list[KeySpec] = []
    _append_row(
        specs,
        0,
        [
            ("`", "`", 1.0),
            ("1", "1", 1.0),
            ("2", "2", 1.0),
            ("3", "3", 1.0),
            ("4", "4", 1.0),
            ("5", "5", 1.0),
            ("6", "6", 1.0),
            ("7", "7", 1.0),
            ("8", "8", 1.0),
            ("9", "9", 1.0),
            ("0", "0", 1.0),
            ("-", "-", 1.0),
            ("=", "=", 1.0),
            ("Backspace", None, 2.0),
        ],
    )
    _append_row(
        specs,
        1,
        [
            ("Tab", None, 1.45),
            ("Q", "q", 1.0),
            ("W", "w", 1.0),
            ("E", "e", 1.0),
            ("R", "r", 1.0),
            ("T", "t", 1.0),
            ("Y", "y", 1.0),
            ("U", "u", 1.0),
            ("I", "i", 1.0),
            ("O", "o", 1.0),
            ("P", "p", 1.0),
            ("[", "[", 1.0),
            ("]", "]", 1.0),
            ("\\", "\\", 1.55),
        ],
    )
    _append_row(
        specs,
        2,
        [
            ("Caps", None, 1.75),
            ("A", "a", 1.0),
            ("S", "s", 1.0),
            ("D", "d", 1.0),
            ("F", "f", 1.0),
            ("G", "g", 1.0),
            ("H", "h", 1.0),
            ("J", "j", 1.0),
            ("K", "k", 1.0),
            ("L", "l", 1.0),
            (";", ";", 1.0),
            ("'", "'", 1.0),
            ("Enter", None, 2.35),
        ],
    )
    _append_row(
        specs,
        3,
        [
            ("Shift", None, 2.25),
            ("Z", "z", 1.0),
            ("X", "x", 1.0),
            ("C", "c", 1.0),
            ("V", "v", 1.0),
            ("B", "b", 1.0),
            ("N", "n", 1.0),
            ("M", "m", 1.0),
            (",", ",", 1.0),
            (".", ".", 1.0),
            ("/", "/", 1.0),
            ("Shift", None, 2.85),
        ],
    )
    # Give duplicate special keys stable ids after row construction.
    corrected: list[KeySpec] = []
    shift_seen = 0
    for spec in specs:
        if spec.text == "Shift":
            shift_seen += 1
            spec_id = "left_shift" if shift_seen == 1 else "right_shift"
            hand, finger = FINGER_BY_KEY_ID[spec_id]
            corrected.append(
                KeySpec(
                    id=spec_id,
                    text=spec.text,
                    value=spec.value,
                    row=spec.row,
                    x=spec.x,
                    width=spec.width,
                    hand=hand,
                    finger=finger,
                    special=True,
                )
            )
        elif spec.text == "Backspace":
            corrected.append(_replace_special(spec, "backspace"))
        elif spec.text == "Tab":
            corrected.append(_replace_special(spec, "tab"))
        elif spec.text == "Caps":
            corrected.append(_replace_special(spec, "caps"))
        elif spec.text == "Enter":
            corrected.append(_replace_special(spec, "enter"))
        else:
            corrected.append(spec)
    _append_row(
        corrected,
        4,
        [
            ("Ctrl", None, 1.25),
            ("Alt", None, 1.25),
            ("Space", " ", 6.65),
            ("Alt", None, 1.25),
            ("Ctrl", None, 1.25),
        ],
    )
    final: list[KeySpec] = []
    alt_seen = 0
    ctrl_seen = 0
    for spec in corrected:
        if spec.text == "Alt":
            alt_seen += 1
            spec_id = "left_alt" if alt_seen == 1 else "right_alt"
            final.append(_replace_special(spec, spec_id, hand="left" if alt_seen == 1 else "right", finger="thumb"))
        elif spec.text == "Ctrl":
            ctrl_seen += 1
            spec_id = "left_ctrl" if ctrl_seen == 1 else "right_ctrl"
            final.append(
                _replace_special(
                    spec,
                    spec_id,
                    hand="left" if ctrl_seen == 1 else "right",
                    finger="pinky",
                )
            )
        else:
            final.append(spec)
    return tuple(final)


def _replace_special(
    spec: KeySpec,
    spec_id: str,
    hand: Hand | None = None,
    finger: Finger | None = None,
) -> KeySpec:
    mapped_hand, mapped_finger = FINGER_BY_KEY_ID.get(spec_id, (hand, finger))
    return KeySpec(
        id=spec_id,
        text=spec.text,
        value=spec.value,
        row=spec.row,
        x=spec.x,
        width=spec.width,
        hand=mapped_hand,
        finger=mapped_finger,
        special=True,
    )


def _spec_by_id() -> dict[str, KeySpec]:
    return {spec.id: spec for spec in get_key_specs()}


def key_id_for_text(text: str) -> str | None:
    if not text:
        return None
    if text in SHIFT_CHAR_MAPPING:
        return _key_id(SHIFT_CHAR_MAPPING[text])
    if text == " ":
        return "space"
    if text.isalpha() and len(text) == 1:
        return text.lower()
    if len(text) == 1:
        return _key_id(text)
    return None


def build_key_guide(target: str) -> KeyGuide:
    if not target:
        raise ValueError("target must not be empty")

    is_zhuyin = target in ZHUYIN_MAPPING.values()
    shift_required = False
    if is_zhuyin:
        base_value = next(key for key, value in ZHUYIN_MAPPING.items() if value == target)
    elif target in SHIFT_CHAR_MAPPING:
        base_value = SHIFT_CHAR_MAPPING[target]
        shift_required = True
    elif target.isalpha():
        base_value = target.lower()
        shift_required = target.isupper()
    else:
        base_value = target

    base_key_id = key_id_for_text(base_value)
    if base_key_id is None:
        raise ValueError(f"unsupported target: {target!r}")

    specs = _spec_by_id()
    spec = specs[base_key_id]
    if not spec.hand or not spec.finger:
        raise ValueError(f"key has no finger mapping: {target!r}")

    shift_key_id: str | None = None
    shift_hand: Hand | None = None
    shift_finger: Finger | None = None
    if shift_required:
        if spec.hand == "left":
            shift_key_id = "right_shift"
        elif spec.hand == "right":
            shift_key_id = "left_shift"
        else:
            shift_key_id = None
        if shift_key_id:
            shift_spec = specs[shift_key_id]
            shift_hand = shift_spec.hand
            shift_finger = shift_spec.finger

    return KeyGuide(
        target=target,
        base_key_id=base_key_id,
        base_key_text=spec.text,
        hand=spec.hand,
        finger=spec.finger,
        shift_key_id=shift_key_id,
        shift_hand=shift_hand,
        shift_finger=shift_finger,
        is_zhuyin=is_zhuyin,
    )


def label_for_key(spec: KeySpec, label_mode: str) -> str:
    if label_mode == "zhuyin" and spec.zhuyin:
        return spec.zhuyin
    if label_mode == "english" and spec.value:
        return spec.text
    if label_mode == "default":
        return spec.text
    return spec.text
