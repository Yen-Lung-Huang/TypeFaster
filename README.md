# TypeFaster

TypeFaster is a keyboard typing practice program with English, Zhuyin, and mixed modes.

The new GUI uses a shared typing core so the same key mapping can later drive the
terminal UI, the PySide6 GUI, or an external hand-control bridge.

## Run the GUI

```powershell
python -m pip install -r requirements.txt
python run_gui.py
```

You can also launch it as a module:

```powershell
python -m typefaster
```

## Qt Creator

Open `pyproject.toml` from Qt Creator. The project includes a
`[tool.pyside6-project]` file list so Qt Creator and `pyside6-project` can see
the Python sources.

If your Qt Creator/PySide6 setup is older and does not recognize
`pyproject.toml`, open `typefaster.pyproject` instead.

The current GUI draws the keyboard and translucent hands with a custom QWidget,
so Qt Creator's visual Designer is still useful for future dialogs/settings
pages, but the main keyboard canvas is intentionally code-driven.

## Controls

- `Esc`: exit
- `F1`: toggle the translucent hand guide
- `F2`: cycle keyboard labels
- `F3`: toggle light/dark theme

The guide uses opposite-hand Shift: left-hand keys use right Shift, and right-hand
keys use left Shift.

The `F` and `J` keys include small tactile ridge markers, matching the home-row
bumps on physical keyboards.
