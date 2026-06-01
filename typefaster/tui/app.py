from __future__ import annotations


def main() -> int:
    try:
        from TypingPractice import TypingPractice
    except ImportError as exc:  # pragma: no cover - depends on optional urwid.
        raise SystemExit("The TUI requires urwid. Install it with: python -m pip install urwid") from exc

    TypingPractice().run()
    return 0
