"""Load game data from JSON files into model objects."""
import json
from pathlib import Path
from models import Creature, Expedition, ExpeditionTier

DATA_DIR = Path(__file__).parent / "data"


def load_creatures(
    path: Path = DATA_DIR / "creatures.json",
    levels_path: Path = DATA_DIR / "creature_levels.json",
) -> list[Creature]:
    """Load creatures roster and their current levels."""
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    with open(levels_path, encoding="utf-8") as f:
        levels = json.load(f)
    return [
        Creature(
            name=c["name"],
            tier=c["tier"],
            type=c["type"],
            trait=c["trait"],
            level=levels[c["name"]]["level"],
            awakening=levels[c["name"]]["awakening"],
            base_stats=c["base_stats"],
            job_proficiencies=c["job_proficiencies"],
        )
        for c in raw
        if c["name"] in levels
    ]


def load_expeditions(
    path: Path = DATA_DIR / "expeditions.json",
    progress_path: Path = DATA_DIR / "expedition_progress.json",
) -> list[Expedition]:
    """Load expedition definitions, filtered to unlocked tiers only."""
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    with open(progress_path, encoding="utf-8") as f:
        progress = json.load(f)
    expeditions = []
    for e in raw:
        unlocked = progress.get(e["name"], 0)
        if unlocked == 0:
            continue
        tiers = [
            ExpeditionTier(
                number=i + 1,
                difficulty=t["difficulty"],
                xp_reward=t["xp_reward"],
            )
            for i, t in enumerate(e["tiers"][:unlocked])
            if t["difficulty"] is not None and t["xp_reward"] is not None
        ]
        if not tiers:
            continue
        expeditions.append(Expedition(
            name=e["name"],
            preferred_types=e["preferred_types"],
            opposing_types=e["opposing_types"],
            preferred_trait=e["preferred_trait"],
            stat_weights=e["stat_weights"],
            tiers=tiers,
        ))
    return expeditions
