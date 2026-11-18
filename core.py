"""
Domain models, Pokémon partner evolution lines, and XP progression rules for Dib.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "public"

XP_PER_FOCUS_MINUTE = 10
XP_PER_LEVEL = 100

LEGACY_KEY_MAP = {
    "coruja": "charmander",
    "passaro": "squirtle",
    "raposa": "bulbasaur",
}


@dataclass(frozen=True)
class EvolutionStage:
    pokedex_id: int
    name: str
    min_level: int
    sprite_name: str

    @property
    def pokedex_code(self) -> str:
        return f"#{self.pokedex_id:03d}"

    @property
    def sprite_path(self) -> Path:
        return ASSETS_DIR / self.sprite_name


@dataclass(frozen=True)
class Companion:
    key: str
    name: str
    element_type: str
    trait: str
    accent_hex: str
    stages: Tuple[EvolutionStage, ...]

    def stage_for_level(self, level: int) -> EvolutionStage:
        current = self.stages[0]
        for stage in self.stages:
            if level >= stage.min_level:
                current = stage
        return current

    def next_evolution(self, level: int) -> Optional[EvolutionStage]:
        for stage in self.stages:
            if stage.min_level > level:
                return stage
        return None

    @property
    def sprite_path(self) -> Path:
        return self.stages[0].sprite_path


COMPANIONS: Dict[str, Companion] = {
    "charmander": Companion(
        key="charmander",
        name="Charmander",
        element_type="FIRE",
        trait="Relentless Drive",
        accent_hex="#EF4444",
        stages=(
            EvolutionStage(4, "Charmander", 1, "pokemon_4.gif"),
            EvolutionStage(5, "Charmeleon", 5, "pokemon_5.gif"),
            EvolutionStage(6, "Charizard", 10, "pokemon_6.gif"),
        ),
    ),
    "bulbasaur": Companion(
        key="bulbasaur",
        name="Bulbasaur",
        element_type="GRASS",
        trait="Steady Growth",
        accent_hex="#10B981",
        stages=(
            EvolutionStage(1, "Bulbasaur", 1, "pokemon_1.gif"),
            EvolutionStage(2, "Ivysaur", 5, "pokemon_2.gif"),
            EvolutionStage(3, "Venusaur", 10, "pokemon_3.gif"),
        ),
    ),
    "squirtle": Companion(
        key="squirtle",
        name="Squirtle",
        element_type="WATER",
        trait="Calm Precision",
        accent_hex="#3B82F6",
        stages=(
            EvolutionStage(7, "Squirtle", 1, "pokemon_7.gif"),
            EvolutionStage(8, "Wartortle", 5, "pokemon_8.gif"),
            EvolutionStage(9, "Blastoise", 10, "pokemon_9.gif"),
        ),
    ),
    "pikachu": Companion(
        key="pikachu",
        name="Pikachu",
        element_type="ELECTRIC",
        trait="High Voltage Focus",
        accent_hex="#F59E0B",
        stages=(
            EvolutionStage(172, "Pichu", 1, "pokemon_172.gif"),
            EvolutionStage(25, "Pikachu", 5, "pokemon_25.gif"),
            EvolutionStage(26, "Raichu", 10, "pokemon_26.gif"),
        ),
    ),
    "gastly": Companion(
        key="gastly",
        name="Gastly",
        element_type="GHOST",
        trait="Night Owl Tactician",
        accent_hex="#8B5CF6",
        stages=(
            EvolutionStage(92, "Gastly", 1, "pokemon_92.gif"),
            EvolutionStage(93, "Haunter", 5, "pokemon_93.gif"),
            EvolutionStage(94, "Gengar", 10, "pokemon_94.gif"),
        ),
    ),
}


def resolve_companion(key: str) -> Companion:
    normalized = LEGACY_KEY_MAP.get(key, key)
    return COMPANIONS.get(normalized, COMPANIONS["charmander"])


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
