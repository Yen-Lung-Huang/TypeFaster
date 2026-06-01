from __future__ import annotations

from dataclasses import dataclass
import math
import sys

try:
    from PySide6.QtCore import QPointF, Qt, QRectF, QTimer
    from PySide6.QtGui import QColor, QFont, QKeyEvent, QPainter, QPainterPath, QPalette, QPen
    from PySide6.QtWidgets import (
        QApplication,
        QButtonGroup,
        QCheckBox,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QSizePolicy,
        QVBoxLayout,
        QWidget,
    )
except ImportError as exc:  # pragma: no cover - exercised only without GUI deps.
    raise SystemExit(
        "PySide6 is required for the GUI. Install it with: python -m pip install PySide6"
    ) from exc

from typefaster.core.layout import (
    LABEL_MODES,
    MODES,
    KeyGuide,
    get_key_specs,
    label_for_key,
)
from typefaster.core.session import PracticeResult, PracticeSession


THEMES = {
    "light": {
        "window_bg": "#f7f8fb",
        "title": "#111827",
        "text": "#1f2937",
        "muted": "#64748b",
        "divider": "#d8dee8",
        "board": "#e7ebf1",
        "key": "#ffffff",
        "key_special": "#eef2f7",
        "key_border": "#c8d0dc",
        "active": "#0f766e",
        "active_border": "#0f5f59",
        "shift": "#f59e0b",
        "shift_border": "#b45309",
        "correct": "#15803d",
        "wrong": "#b91c1c",
        "button_checked": "#1f2937",
        "left_hand": "#3b82f6",
        "left_hand_active": "#2563eb",
        "right_hand": "#ec4899",
        "right_hand_active": "#db2777",
        "hand_outline": "#64748b",
        "finger_pinky": "#ef476f",
        "finger_ring": "#f59e0b",
        "finger_middle": "#10b981",
        "finger_index": "#3b82f6",
        "finger_thumb": "#8b5cf6",
    },
    "dark": {
        "window_bg": "#171717",
        "title": "#f5f5f4",
        "text": "#e7e5e4",
        "muted": "#a8a29e",
        "divider": "#3f3f46",
        "board": "#242424",
        "key": "#2f3136",
        "key_special": "#26282d",
        "key_border": "#555b66",
        "active": "#14b8a6",
        "active_border": "#5eead4",
        "shift": "#d97706",
        "shift_border": "#fbbf24",
        "correct": "#22c55e",
        "wrong": "#ef4444",
        "button_checked": "#0f766e",
        "left_hand": "#60a5fa",
        "left_hand_active": "#93c5fd",
        "right_hand": "#f472b6",
        "right_hand_active": "#f9a8d4",
        "hand_outline": "#94a3b8",
        "finger_pinky": "#fb7185",
        "finger_ring": "#fbbf24",
        "finger_middle": "#34d399",
        "finger_index": "#60a5fa",
        "finger_thumb": "#a78bfa",
    },
}


@dataclass(frozen=True)
class FingerRig:
    mcp: QPointF
    pip: QPointF
    dip: QPointF
    tip: QPointF
    base_width: float
    mid_width: float
    tip_width: float


class KeyboardCanvas(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.key_specs = get_key_specs()
        self.key_rects: dict[str, QRectF] = {}
        self.guide: KeyGuide | None = None
        self.label_mode = "default"
        self.practice_mode = "english"
        self.show_hands = True
        self.theme = "light"
        self.flash_key_id: str | None = None
        self.flash_correct: bool | None = None
        self.setMinimumHeight(360)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_guide(self, guide: KeyGuide) -> None:
        self.guide = guide
        self.update()

    def set_label_mode(self, label_mode: str) -> None:
        self.label_mode = label_mode
        self.update()

    def set_practice_mode(self, practice_mode: str) -> None:
        self.practice_mode = practice_mode
        self.update()

    def set_show_hands(self, show_hands: bool) -> None:
        self.show_hands = show_hands
        self.update()

    def set_theme(self, theme: str) -> None:
        self.theme = theme
        self.update()

    def flash_result(self, result: PracticeResult) -> None:
        self.flash_key_id = result.typed_key_id or result.target_guide.base_key_id
        self.flash_correct = result.correct
        self.update()

    def clear_flash(self) -> None:
        self.flash_key_id = None
        self.flash_correct = None
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt override
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), self._color("window_bg"))

        self._layout_keys()
        self._draw_keyboard_base(painter)
        self._draw_key_faces(painter)
        if self.show_hands:
            self._draw_hands(painter)
        self._draw_key_labels(painter)

    def _layout_keys(self) -> None:
        row_count = max(spec.row for spec in self.key_specs) + 1
        row_widths = {
            row: max(spec.x + spec.width for spec in self.key_specs if spec.row == row)
            for row in range(row_count)
        }
        max_units = max(row_widths.values())
        row_offsets = {row: (max_units - width) / 2.0 for row, width in row_widths.items()}
        gap_units = 0.14

        margin_x = 28.0
        margin_y = 28.0
        available_w = max(1.0, self.width() - margin_x * 2)
        available_h = max(1.0, self.height() - margin_y * 2)
        unit_from_w = available_w / max_units
        unit_from_h = available_h / (row_count + gap_units * (row_count - 1))
        unit = min(unit_from_w, unit_from_h)
        key_h = unit * 0.86
        gap = unit * gap_units
        total_w = max_units * unit
        total_h = row_count * key_h + (row_count - 1) * gap
        start_x = (self.width() - total_w) / 2.0
        start_y = (self.height() - total_h) / 2.0

        self.key_rects.clear()
        for spec in self.key_specs:
            x = start_x + (row_offsets[spec.row] + spec.x) * unit
            y = start_y + spec.row * (key_h + gap)
            width = spec.width * unit - gap * 0.45
            self.key_rects[spec.id] = QRectF(x, y, width, key_h)

    def _draw_keyboard_base(self, painter: QPainter) -> None:
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._color("board"))
        board = self._keyboard_bounds().adjusted(-16, -16, 16, 16)
        painter.drawRoundedRect(board, 18, 18)
        painter.restore()

    def _draw_key_faces(self, painter: QPainter) -> None:
        active_ids = set()
        if self.guide:
            active_ids.add(self.guide.base_key_id)
            if self.guide.shift_key_id:
                active_ids.add(self.guide.shift_key_id)

        for spec in self.key_specs:
            rect = self.key_rects[spec.id]
            fill = self._color("key")
            border = self._color("key_border")

            if spec.id == self.flash_key_id and self.flash_correct is not None:
                fill = self._color("correct") if self.flash_correct else self._color("wrong")
                border = fill.darker(120)
            elif spec.id in active_ids:
                if self.guide and spec.id == self.guide.shift_key_id:
                    fill = self._color("shift")
                    border = self._color("shift_border")
                else:
                    fill = self._target_finger_color(alpha=220)
                    border = self._target_finger_color(alpha=255)
            elif spec.special:
                fill = self._color("key_special")

            painter.save()
            painter.setPen(QPen(border, 1.2))
            painter.setBrush(fill)
            painter.drawRoundedRect(rect, 7, 7)

            painter.restore()

    def _draw_key_labels(self, painter: QPainter) -> None:
        active_ids = set()
        if self.guide:
            active_ids.add(self.guide.base_key_id)
            if self.guide.shift_key_id:
                active_ids.add(self.guide.shift_key_id)

        for spec in self.key_specs:
            rect = self.key_rects[spec.id]
            text = self._color("text")
            if spec.id == self.flash_key_id and self.flash_correct is not None:
                text = QColor("#ffffff")
            elif spec.id in active_ids:
                text = QColor("#ffffff")

            painter.save()
            font = QFont("Segoe UI", max(8, int(rect.height() * 0.28)))
            if spec.width > 1.8:
                font.setPointSize(max(8, int(rect.height() * 0.24)))
            font.setBold(spec.id in active_ids)
            painter.setFont(font)
            painter.setPen(text)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, label_for_key(spec, self._effective_label_mode()))
            if spec.id in {"f", "j"}:
                ridge = QColor(text)
                ridge.setAlpha(180)
                ridge_rect = QRectF(
                    rect.center().x() - rect.width() * 0.14,
                    rect.bottom() - rect.height() * 0.19,
                    rect.width() * 0.28,
                    max(2.0, rect.height() * 0.035),
                )
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(ridge)
                painter.drawRoundedRect(ridge_rect, 2, 2)
            painter.restore()

    def _effective_label_mode(self) -> str:
        if self.label_mode != "default":
            return self.label_mode
        if self.practice_mode == "zhuyin":
            return "zhuyin"
        return "english"

    def _draw_hands(self, painter: QPainter) -> None:
        if not self.key_rects:
            return

        active_fingers = set()
        if self.guide:
            active_fingers.add(self.guide.finger_id)
            if self.guide.shift_finger_id:
                active_fingers.add(self.guide.shift_finger_id)

        self._draw_hand_guide(painter, "left", active_fingers)
        self._draw_hand_guide(painter, "right", active_fingers)

    def _draw_hand_guide(self, painter: QPainter, hand: str, active_fingers: set[str]) -> None:
        home = {
            "left": {
                "pinky": "a",
                "ring": "s",
                "middle": "d",
                "index": "f",
                "thumb": "space",
            },
            "right": {
                "index": "j",
                "middle": "k",
                "ring": "l",
                "pinky": "semicolon",
                "thumb": "space",
            },
        }[hand]

        key_h = self.key_rects["a"].height()
        palm_fill = self._color("hand_outline", 7)
        outline_color = self._color("hand_outline", 120)
        joint_color = self._color("hand_outline", 88)

        if hand == "left":
            palm_left = self.key_rects["z"].left() - key_h * 0.35
            palm_right = self.key_rects["v"].right() + key_h * 0.35
        else:
            palm_left = self.key_rects["n"].left() - key_h * 0.35
            palm_right = self.key_rects["slash"].right() + key_h * 0.35
        palm_top = self.key_rects["space"].top() - key_h * 0.22
        palm_rect = QRectF(palm_left, palm_top, palm_right - palm_left, key_h * 1.55)

        painter.save()
        self._draw_palm_shape(painter, hand, palm_rect, palm_fill, outline_color, key_h)

        for finger, home_key_id in home.items():
            finger_id = f"{hand}_{finger}"
            target_key = self._finger_target_key(hand, finger, home_key_id)
            is_active = finger_id in active_fingers
            home_tip = self._finger_anchor(hand, finger, home_key_id)
            tip = self._finger_anchor(hand, finger, target_key)
            rig = self._build_finger_rig(hand, finger, palm_rect, tip, key_h)
            finger_color = self._color(f"finger_{finger}", 172 if is_active else 112)
            finger_fill = self._color(f"finger_{finger}", 28 if is_active else 9)
            self._draw_finger_rig(painter, rig, finger_fill, finger_color, key_h)

            if not is_active:
                self._draw_joint_marker(painter, home_tip, joint_color, key_h * 0.055)
                continue

            if target_key != home_key_id:
                painter.setPen(
                    QPen(
                        finger_color,
                        max(2.0, key_h * 0.045),
                        Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap,
                    )
                )
                painter.drawLine(home_tip, tip)

            self._draw_contact_halo(painter, tip, finger_color, key_h)
        painter.restore()

    @staticmethod
    def _finger_base_point(hand: str, finger: str, palm_rect: QRectF) -> QPointF:
        offset = {
            "pinky": 0.18,
            "ring": 0.34,
            "middle": 0.5,
            "index": 0.68,
            "thumb": 0.28 if hand == "left" else 0.72,
        }[finger]
        if hand == "right" and finger != "thumb":
            offset = 1.0 - offset
        y_factor = 0.18 if finger != "thumb" else 0.6
        return QPointF(palm_rect.left() + palm_rect.width() * offset, palm_rect.top() + palm_rect.height() * y_factor)

    @staticmethod
    def _finger_width(finger: str, key_h: float) -> float:
        return {
            "pinky": key_h * 0.18,
            "ring": key_h * 0.19,
            "middle": key_h * 0.2,
            "index": key_h * 0.21,
            "thumb": key_h * 0.28,
        }[finger]

    def _build_finger_rig(
        self,
        hand: str,
        finger: str,
        palm_rect: QRectF,
        tip: QPointF,
        key_h: float,
    ) -> FingerRig:
        mcp = self._finger_base_point(hand, finger, palm_rect)
        dx = tip.x() - mcp.x()
        dy = tip.y() - mcp.y()
        length = max(1.0, math.hypot(dx, dy))
        ux = dx / length
        uy = dy / length
        normal = QPointF(-uy, ux)
        curl = key_h * (0.18 if finger != "thumb" else 0.04)
        side = 1 if hand == "left" else -1
        if finger == "thumb":
            side *= -1
        pip = QPointF(mcp.x() + dx * 0.42 + normal.x() * curl * side, mcp.y() + dy * 0.34 + normal.y() * curl * side)
        dip = QPointF(mcp.x() + dx * 0.72 + normal.x() * curl * 0.55 * side, mcp.y() + dy * 0.66 + normal.y() * curl * 0.55 * side)
        base_width = self._finger_width(finger, key_h)
        return FingerRig(
            mcp=mcp,
            pip=pip,
            dip=dip,
            tip=tip,
            base_width=base_width,
            mid_width=base_width * 0.78,
            tip_width=base_width * (0.56 if finger != "thumb" else 0.68),
        )

    def _finger_anchor(self, hand: str, finger: str, key_id: str):
        rect = self.key_rects[key_id]
        pos = rect.center()
        if finger == "thumb":
            pos.setY(rect.center().y() + rect.height() * 0.24)
            if key_id == "space":
                if hand == "left":
                    pos.setX(rect.center().x() - rect.width() * 0.23)
                else:
                    pos.setX(rect.center().x() + rect.width() * 0.23)
        else:
            pos.setY(rect.center().y() + rect.height() * 0.12)
        return pos

    def _draw_palm_shape(
        self,
        painter: QPainter,
        hand: str,
        rect: QRectF,
        fill: QColor,
        outline: QColor,
        key_h: float,
    ) -> None:
        left = rect.left()
        right = rect.right()
        top = rect.top()
        bottom = rect.bottom()
        width = rect.width()
        height = rect.height()
        mirror = -1 if hand == "right" else 1
        cx = rect.center().x()

        def px(normalized_x: float) -> float:
            return cx + mirror * (normalized_x - 0.5) * width

        path = QPainterPath()
        path.moveTo(px(0.09), bottom - height * 0.08)
        path.cubicTo(px(0.04), bottom + height * 0.13, px(0.13), bottom + height * 0.4, px(0.25), bottom + height * 0.56)
        path.cubicTo(px(0.35), bottom + height * 0.68, px(0.43), bottom + height * 0.48, px(0.48), bottom + height * 0.3)
        path.cubicTo(px(0.56), bottom + height * 0.02, px(0.72), top + height * 0.72, px(0.88), top + height * 0.46)
        path.cubicTo(px(0.99), top + height * 0.28, px(0.92), top + height * 0.03, px(0.78), top + height * 0.03)
        path.cubicTo(px(0.62), top - height * 0.03, px(0.28), top - height * 0.02, px(0.15), top + height * 0.24)
        path.cubicTo(px(0.05), top + height * 0.42, px(0.02), top + height * 0.72, px(0.09), bottom - height * 0.08)
        path.closeSubpath()

        painter.save()
        painter.setPen(QPen(outline, max(1.8, key_h * 0.032)))
        painter.setBrush(fill)
        painter.drawPath(path)
        painter.restore()

    @staticmethod
    def _draw_finger_rig(
        painter: QPainter,
        rig: FingerRig,
        fill: QColor,
        outline: QColor,
        key_h: float,
    ) -> None:
        def normal(a: QPointF, b: QPointF) -> QPointF:
            dx = b.x() - a.x()
            dy = b.y() - a.y()
            length = max(1.0, math.hypot(dx, dy))
            return QPointF(-dy / length, dx / length)

        n0 = normal(rig.mcp, rig.pip)
        n1 = normal(rig.pip, rig.dip)
        n2 = normal(rig.dip, rig.tip)

        left_mcp = QPointF(rig.mcp.x() + n0.x() * rig.base_width, rig.mcp.y() + n0.y() * rig.base_width)
        left_pip = QPointF(rig.pip.x() + n1.x() * rig.mid_width, rig.pip.y() + n1.y() * rig.mid_width)
        left_dip = QPointF(rig.dip.x() + n2.x() * rig.mid_width * 0.72, rig.dip.y() + n2.y() * rig.mid_width * 0.72)
        left_tip = QPointF(rig.tip.x() + n2.x() * rig.tip_width, rig.tip.y() + n2.y() * rig.tip_width)

        right_mcp = QPointF(rig.mcp.x() - n0.x() * rig.base_width, rig.mcp.y() - n0.y() * rig.base_width)
        right_pip = QPointF(rig.pip.x() - n1.x() * rig.mid_width, rig.pip.y() - n1.y() * rig.mid_width)
        right_dip = QPointF(rig.dip.x() - n2.x() * rig.mid_width * 0.72, rig.dip.y() - n2.y() * rig.mid_width * 0.72)
        right_tip = QPointF(rig.tip.x() - n2.x() * rig.tip_width, rig.tip.y() - n2.y() * rig.tip_width)

        path = QPainterPath()
        path.moveTo(left_mcp)
        path.cubicTo(left_pip, left_dip, left_tip)
        path.quadTo(rig.tip, right_tip)
        path.cubicTo(right_dip, right_pip, right_mcp)
        path.quadTo(rig.mcp, left_mcp)
        path.closeSubpath()

        painter.save()
        painter.setPen(QPen(outline, max(1.7, key_h * 0.028)))
        painter.setBrush(fill)
        painter.drawPath(path)
        joint_pen = QColor(outline)
        joint_pen.setAlpha(max(35, outline.alpha() - 45))
        painter.setPen(QPen(joint_pen, max(1.0, key_h * 0.015)))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for point, radius in ((rig.pip, rig.mid_width * 0.18), (rig.dip, rig.tip_width * 0.2)):
            painter.drawEllipse(point, radius, radius)
        painter.restore()

    @staticmethod
    def _draw_joint_marker(painter: QPainter, point: QPointF, color: QColor, radius: float) -> None:
        painter.save()
        painter.setPen(QPen(color, 1.1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(point, radius, radius)
        painter.restore()

    @staticmethod
    def _draw_contact_halo(painter: QPainter, point: QPointF, color: QColor, key_h: float) -> None:
        painter.save()
        halo = QColor(color)
        halo.setAlpha(42)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(halo)
        painter.drawEllipse(point, key_h * 0.23, key_h * 0.23)
        painter.setPen(QPen(color, max(2.0, key_h * 0.035)))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(point, key_h * 0.12, key_h * 0.12)
        painter.restore()

    def _finger_target_key(self, hand: str, finger: str, fallback_key_id: str) -> str:
        if not self.guide:
            return fallback_key_id
        if self.guide.finger_id == f"{hand}_{finger}":
            return self.guide.base_key_id
        if self.guide.shift_finger_id == f"{hand}_{finger}" and self.guide.shift_key_id:
            return self.guide.shift_key_id
        return fallback_key_id

    def _keyboard_bounds(self) -> QRectF:
        if not self.key_rects:
            return QRectF()
        left = min(rect.left() for rect in self.key_rects.values())
        top = min(rect.top() for rect in self.key_rects.values())
        right = max(rect.right() for rect in self.key_rects.values())
        bottom = max(rect.bottom() for rect in self.key_rects.values())
        return QRectF(left, top, right - left, bottom - top)

    def _color(self, name: str, alpha: int | None = None) -> QColor:
        color = QColor(THEMES[self.theme][name])
        if alpha is not None:
            color.setAlpha(alpha)
        return color

    def _target_finger_color(self, alpha: int | None = None) -> QColor:
        if not self.guide:
            return self._color("active", alpha)
        return self._color(f"finger_{self.guide.finger}", alpha)


class TypeFasterWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        app = QApplication.instance()
        if app is not None:
            app.setStyle("Fusion")
        self.session = PracticeSession()
        self.theme = "light"
        self.result_timer = QTimer(self)
        self.result_timer.setSingleShot(True)
        self.result_timer.timeout.connect(self._clear_result_flash)

        self.setWindowTitle("TypeFaster")
        self.setObjectName("rootWindow")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        self.setMinimumSize(980, 680)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.target_label = QLabel()
        self.target_label.setObjectName("targetLabel")
        self.stats_label = QLabel()
        self.guide_label = QLabel()
        self.canvas = KeyboardCanvas()

        self.mode_group = self._build_button_group(MODES, self._set_mode)
        self.label_group = self._build_button_group(LABEL_MODES, self._set_label_mode)
        self.dark_checkbox = QCheckBox("Dark")
        self.dark_checkbox.toggled.connect(self._toggle_theme)
        self.hands_checkbox = QCheckBox("Hands")
        self.hands_checkbox.setChecked(True)
        self.hands_checkbox.toggled.connect(self.canvas.set_show_hands)

        self._build_layout()
        self._apply_styles()
        self._sync_view()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802 - Qt override
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        if event.key() == Qt.Key.Key_F1:
            self.hands_checkbox.setChecked(not self.hands_checkbox.isChecked())
            return
        if event.key() == Qt.Key.Key_F2:
            self._cycle_label_mode()
            return
        if event.key() == Qt.Key.Key_F3:
            self.dark_checkbox.setChecked(not self.dark_checkbox.isChecked())
            return

        text = event.text()
        if len(text) != 1 or event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            return

        result = self.session.submit(text)
        if result is None:
            return
        self.canvas.flash_result(result)
        self._sync_view(result)
        self.result_timer.start(140)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt override
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(THEMES[self.theme]["window_bg"]))
        super().paintEvent(event)

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt override
        self.setFocus()
        super().mousePressEvent(event)

    def _build_layout(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 24)
        root.setSpacing(16)

        header = QHBoxLayout()
        header.setSpacing(18)
        title = QLabel("TypeFaster")
        title.setObjectName("titleLabel")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self._panel("Mode", self.mode_group.buttons()))
        header.addWidget(self._panel("Labels", self.label_group.buttons()))
        header.addWidget(self.dark_checkbox)
        header.addWidget(self.hands_checkbox)
        root.addLayout(header)

        info = QGridLayout()
        info.setHorizontalSpacing(18)
        info.setVerticalSpacing(8)
        info.addWidget(QLabel("Target"), 0, 0)
        info.addWidget(QLabel("Stats"), 0, 1)
        info.addWidget(QLabel("Guide"), 0, 2)
        info.addWidget(self.target_label, 1, 0)
        info.addWidget(self.stats_label, 1, 1)
        info.addWidget(self.guide_label, 1, 2)
        info.setColumnStretch(0, 1)
        info.setColumnStretch(1, 1)
        info.setColumnStretch(2, 2)
        root.addLayout(info)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setObjectName("divider")
        root.addWidget(line)
        root.addWidget(self.canvas, 1)

        footer = QLabel("Esc exit  |  F1 hands  |  F2 labels  |  F3 theme")
        footer.setObjectName("footerLabel")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(footer)

    def _panel(self, label: str, buttons: list[QPushButton]) -> QWidget:
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        caption = QLabel(label)
        caption.setObjectName("panelCaption")
        layout.addWidget(caption)
        for button in buttons:
            layout.addWidget(button)
        return panel

    def _build_button_group(self, values: tuple[str, ...], callback) -> QButtonGroup:
        group = QButtonGroup(self)
        group.setExclusive(True)
        for index, value in enumerate(values):
            button = QPushButton(value.capitalize())
            button.setCheckable(True)
            button.setProperty("value", value)
            button.clicked.connect(lambda checked=False, b=button: callback(b.property("value")))
            group.addButton(button)
            if index == 0:
                button.setChecked(True)
        return group

    def _set_mode(self, mode: str) -> None:
        self.session.set_mode(mode)
        self._sync_view()
        self.setFocus()

    def _set_label_mode(self, label_mode: str) -> None:
        self.canvas.set_label_mode(label_mode)
        self.setFocus()

    def _cycle_label_mode(self) -> None:
        buttons = self.label_group.buttons()
        current_index = next((i for i, button in enumerate(buttons) if button.isChecked()), 0)
        next_button = buttons[(current_index + 1) % len(buttons)]
        next_button.setChecked(True)
        self._set_label_mode(next_button.property("value"))

    def _toggle_theme(self, enabled: bool) -> None:
        self.theme = "dark" if enabled else "light"
        self.canvas.set_theme(self.theme)
        self._apply_styles()
        self.setFocus()

    def _clear_result_flash(self) -> None:
        self.canvas.clear_flash()
        self.stats_label.setProperty("state", "")
        self.stats_label.style().unpolish(self.stats_label)
        self.stats_label.style().polish(self.stats_label)

    def _sync_view(self, result: PracticeResult | None = None) -> None:
        guide = self.session.current_guide
        self.canvas.set_practice_mode(self.session.mode)
        self.canvas.set_guide(guide)
        target = self.session.current_target
        if target == " ":
            target_text = "Space"
        else:
            target_text = target
        self.target_label.setText(target_text)
        self.stats_label.setText(
            f"Accuracy {self.session.accuracy:.1f}%   {self.session.correct_count}/{self.session.total_count}"
        )
        self.guide_label.setText(guide.instruction)

        if result is not None:
            self.stats_label.setProperty("state", "correct" if result.correct else "wrong")
        else:
            self.stats_label.setProperty("state", "")
        self.stats_label.style().unpolish(self.stats_label)
        self.stats_label.style().polish(self.stats_label)

    def _apply_styles(self) -> None:
        theme = THEMES[self.theme]
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(theme["window_bg"]))
        palette.setColor(QPalette.ColorRole.Base, QColor(theme["window_bg"]))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(theme["text"]))
        palette.setColor(QPalette.ColorRole.Text, QColor(theme["text"]))
        palette.setColor(QPalette.ColorRole.Button, QColor(theme["key"]))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(theme["text"]))
        self.setPalette(palette)
        self.setStyleSheet(
            f"""
            #rootWindow {{
                background: {theme["window_bg"]};
                color: {theme["text"]};
            }}
            QWidget {{
                background: {theme["window_bg"]};
                color: {theme["text"]};
                font-family: "Segoe UI", "Microsoft JhengHei UI", sans-serif;
                font-size: 14px;
            }}
            QLabel {{
                background: transparent;
            }}
            #titleLabel {{
                font-size: 24px;
                font-weight: 700;
                color: {theme["title"]};
            }}
            #targetLabel {{
                font-size: 44px;
                font-weight: 800;
                color: {theme["active"]};
                padding: 8px 0;
            }}
            #footerLabel,
            #panelCaption {{
                color: {theme["muted"]};
            }}
            #divider {{
                color: {theme["divider"]};
            }}
            QPushButton {{
                background-color: {theme["key"]};
                color: {theme["text"]};
                border: 1px solid {theme["key_border"]};
                border-radius: 7px;
                padding: 6px 11px;
            }}
            QPushButton:checked {{
                background-color: {theme["button_checked"]};
                color: #ffffff;
                border-color: {theme["button_checked"]};
            }}
            QPushButton:hover:!checked {{
                background-color: {theme["key_special"]};
            }}
            QCheckBox {{
                spacing: 8px;
            }}
            QLabel[state="correct"] {{
                color: {theme["correct"]};
                font-weight: 700;
            }}
            QLabel[state="wrong"] {{
                color: {theme["wrong"]};
                font-weight: 700;
            }}
            """
        )


def main() -> int:
    app = QApplication(sys.argv)
    window = TypeFasterWindow()
    window.show()
    window.raise_()
    window.activateWindow()
    window.setFocus()
    return app.exec()
