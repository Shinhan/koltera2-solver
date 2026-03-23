"""Score, time, and XP/s calculations."""
from math import floor
from models import Creature, Expedition, ExpeditionTier, STATS


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
