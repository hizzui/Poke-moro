"""
Domain models and XP progression rules for Dib.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "public"

XP_PER_FOCUS_MINUTE = 10
XP_PER_LEVEL = 100


@dataclass(frozen=True)
class Companion:
    key: str
    name: str
    trait: str
    accent_hex: str
    sprite_name: str

    @property
    def sprite_path(self) -> Path:
        return ASSETS_DIR / self.sprite_name


COMPANIONS: Dict[str, Companion] = {
    "passaro": Companion(
        key="passaro",
        name="Pássaro",
        trait="Criativo",
        accent_hex="#60A5FA",
        sprite_name="passaro.gif",
    ),
    "coruja": Companion(
        key="coruja",
        name="Coruja",
        trait="Sábio",
        accent_hex="#D97706",
        sprite_name="coruja.gif",
    ),
    "raposa": Companion(
        key="raposa",
        name="Raposa",
        trait="Estratégico",
        accent_hex="#FB923C",
        sprite_name="raposa.gif",
    ),
}


@dataclass(frozen=True)
class LevelProgress:
    level: int
    total_xp: int
    current_level_xp: int
    next_level_xp: int
    progress_ratio: float


def compute_level(total_xp: int) -> LevelProgress:
    """Convert cumulative XP into current level and progress bar ratio (0.0 to 1.0)."""
    safe_xp = max(0, int(total_xp))
    level = (safe_xp // XP_PER_LEVEL) + 1
    current_xp = safe_xp % XP_PER_LEVEL
    ratio = current_xp / XP_PER_LEVEL
    return LevelProgress(
        level=level,
        total_xp=safe_xp,
        current_level_xp=current_xp,
        next_level_xp=XP_PER_LEVEL,
        progress_ratio=round(ratio, 4),
    )


def calculate_session_xp(focus_minutes: int) -> int:
    """Award XP proportional to completed focus minutes."""
    return max(0, int(focus_minutes)) * XP_PER_FOCUS_MINUTE
