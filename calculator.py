"""Score, time, and XP/s calculations."""
from math import floor
from models import (
    Creature, Expedition, ExpeditionTier, STATS,
    DUNGEON_STAT_WEIGHTS, DUNGEON_DIFFICULTIES, DUNGEON_XP_RATES,
    DungeonTierResult,
)


def creature_score(creature: Creature, expedition: Expedition) -> int:
    """Compute a single creature's expedition score with type/trait multipliers."""
    stats = creature.stats
    base = sum(stats[s] * expedition.stat_weights[s] for s in STATS)
    score = floor(base)
    if creature.type in expedition.preferred_types:
        score *= 1.5
    if creature.type in expedition.opposing_types:
        score *= 0.5
    if creature.trait == expedition.preferred_trait:
        score *= 1.5
    return floor(score)


def party_score(creatures: list[Creature], expedition: Expedition) -> int:
    """Sum of creature scores for the given party."""
    return sum(creature_score(c, expedition) for c in creatures)


def completion_time(ps: int, difficulty: int) -> float:
    """Expedition duration in minutes (minimum 5)."""
    return max(5.0, 60.0 - 55.0 * ps / difficulty)


def xp_per_second(creatures: list[Creature], expedition: Expedition, tier: ExpeditionTier) -> float:
    """XP per second earned by this party on this expedition tier."""
    ps = party_score(creatures, expedition)
    t = completion_time(ps, tier.difficulty)
    return tier.xp_reward / (len(creatures) * t * 60.0)


# Grade thresholds: score / difficulty ratio boundaries (inclusive lower bound)
_GRADE_THRESHOLDS = [
    ("S", 2.0),
    ("A", 1.0),
    ("B", 0.6),
    ("C", 0.25),
    ("F", 0.0),
]
_GRADE_MULT = {"S": 2.0, "A": 1.5, "B": 1.0, "C": 0.5, "F": 0.25}


def dungeon_grade(score: int, difficulty: int) -> str:
    """Grade (S/A/B/C/F) based on score vs difficulty."""
    ratio = score / difficulty
    for grade, threshold in _GRADE_THRESHOLDS:
        if ratio >= threshold:
            return grade
    return "F"


def creature_dungeon_score(creature: Creature, dungeon_type: str) -> int:
    """Sum of relevant stats for this creature in the given dungeon type."""
    stats = creature.stats
    return sum(stats[s] for s in DUNGEON_STAT_WEIGHTS[dungeon_type])


def dungeon_tier_results(party_dungeon_score: int, dungeon_type: str) -> list[DungeonTierResult]:
    """Compute grade, XP, and runes for all 5 dungeon tiers given a party score."""
    results = []
    for i, (difficulty, base_xp) in enumerate(zip(DUNGEON_DIFFICULTIES, DUNGEON_XP_RATES)):
        tier_number = i + 1
        grade = dungeon_grade(party_dungeon_score, difficulty)
        mult = _GRADE_MULT[grade]
        xp_rate = base_xp * mult
        if dungeon_type == "combat":
            rune_base = tier_number * 2
            chronicle_runes = max(1, floor(rune_base * mult))
        else:
            chronicle_runes = None
        results.append(DungeonTierResult(
            tier_number=tier_number,
            difficulty=difficulty,
            grade=grade,
            xp_rate=xp_rate,
            chronicle_runes=chronicle_runes,
        ))
    return results
