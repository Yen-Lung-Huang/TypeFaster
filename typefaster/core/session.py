from __future__ import annotations

from dataclasses import dataclass
import random
import string

from typefaster.core.layout import (
    MODES,
    ZHUYIN_MAPPING,
    KeyGuide,
    build_key_guide,
    key_id_for_text,
)

ENGLISH_TARGETS = string.ascii_letters + string.digits + string.punctuation + " "


@dataclass(frozen=True)
class PracticeResult:
    target: str
    typed: str
    correct: bool
    target_guide: KeyGuide
    typed_key_id: str | None
    next_target: str
    next_guide: KeyGuide
    correct_count: int
    total_count: int


class PracticeSession:
    def __init__(self, mode: str = "english", rng: random.Random | None = None) -> None:
        if mode not in MODES:
            raise ValueError(f"unsupported mode: {mode}")
        self.rng = rng or random.Random()
        self.mode = mode
        self.correct_count = 0
        self.total_count = 0
        self.current_target = self._generate_target()

    @property
    def accuracy(self) -> float:
        if self.total_count == 0:
            return 0.0
        return self.correct_count / self.total_count * 100.0

    @property
    def current_guide(self) -> KeyGuide:
        return build_key_guide(self.current_target)

    def reset(self) -> None:
        self.correct_count = 0
        self.total_count = 0
        self.current_target = self._generate_target()

    def set_mode(self, mode: str) -> None:
        if mode not in MODES:
            raise ValueError(f"unsupported mode: {mode}")
        self.mode = mode
        self.reset()

    def submit(self, typed: str) -> PracticeResult | None:
        if len(typed) != 1:
            return None
        target = self.current_target
        target_guide = self.current_guide
        correct = self._matches_target(target, typed)

        self.total_count += 1
        if correct:
            self.correct_count += 1
            self.current_target = self._generate_target()

        return PracticeResult(
            target=target,
            typed=typed,
            correct=correct,
            target_guide=target_guide,
            typed_key_id=key_id_for_text(typed),
            next_target=self.current_target,
            next_guide=self.current_guide,
            correct_count=self.correct_count,
            total_count=self.total_count,
        )

    def _generate_target(self) -> str:
        target_mode = self.mode
        if target_mode == "mixed":
            target_mode = self.rng.choice(("english", "zhuyin"))

        if target_mode == "zhuyin":
            return self.rng.choice(tuple(ZHUYIN_MAPPING.values()))
        return self.rng.choice(ENGLISH_TARGETS)

    @staticmethod
    def _matches_target(target: str, typed: str) -> bool:
        if target in ZHUYIN_MAPPING.values():
            return ZHUYIN_MAPPING.get(typed.lower()) == target
        return typed == target
