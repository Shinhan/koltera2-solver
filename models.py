"""Data model dataclasses for creatures, expeditions, and solver results."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

STATS = ["POW", "GRT", "AGI", "SMT", "LOT", "LCK"]
JOBS = ["Chopping", "Mining", "Exploring", "Digging", "Fishing", "Farming"]
DUNGEON_TYPES = ["combat", "chopping", "mining", "digging", "farming", "fishing", "exploring"]

# Stat weights per dungeon type
DUNGEON_STAT_WEIGHTS: dict[str, list[str]] = {
    "combat": ["POW", "GRT", "AGI", "SMT"],
}
for _d in DUNGEON_TYPES:
    if _d != "combat":
        DUNGEON_STAT_WEIGHTS[_d] = ["SMT", "LOT", "LCK"]

DUNGEON_DIFFICULTIES = [2000, 4000, 6000, 8000, 10000]
DUNGEON_XP_RATES = [0.5, 1.0, 1.5, 2.0, 2.5]  # base XP rate per tier


@dataclass
class Creature:
    """A creature in the player's roster."""
    name: str
    tier: int
    type: str
    trait: str
    level: int
    awakening: int
    base_stats: dict[str, int]
    job_proficiencies: dict[str, Optional[int]]

    @property
    def stats(self) -> dict[str, int]:
        """Scaled stats at current level."""
        return {s: self.base_stats[s] * self.level for s in STATS}

    def proficiency(self, job: str) -> int:
        """Job proficiency (0 if not set)."""
        return self.job_proficiencies.get(job) or 0


@dataclass
class ExpeditionTier:
    """One difficulty tier of an expedition."""
    number: int       # 1-based original position in JSON
    difficulty: int
    xp_reward: int


@dataclass
class Expedition:
    """An expedition with its preferred types, trait, stat weights, and unlocked tiers."""
    name: str
    preferred_types: list[str]
    opposing_types: list[str]
    preferred_trait: str
    stat_weights: dict[str, float]
    tiers: list[ExpeditionTier]   # only unlocked tiers


@dataclass
class MachineAssignment:
    """A creature assigned to a machine slot."""
    machine: str
    creature: Creature


@dataclass
class JobAssignment:
    """A creature assigned to a job slot."""
    job: str
    creature: Creature


@dataclass
class ExpeditionAssignment:
    """A party assigned to an expedition tier, with precomputed metrics."""
    expedition: Expedition
    tier: ExpeditionTier
    party: list[Creature]
    xp_per_second: float
    time_minutes: float


@dataclass
class DungeonTierResult:
    """Computed result for one dungeon difficulty tier."""
    tier_number: int       # 1-5
    difficulty: int
    grade: str             # S / A / B / C / F
    xp_rate: float         # base XP rate × grade multiplier
    chronicle_runes: Optional[int]  # combat dungeon only; None otherwise


@dataclass
class DungeonAssignment:
    """Three creatures assigned to the dungeon, with per-tier results."""
    dungeon_type: str
    party: list[Creature]
    party_score: int
    tier_results: list[DungeonTierResult]


@dataclass
class SolverResult:
    """Complete solver output: sanctuary, job assignments, expedition assignments, and leftovers."""
    sanctuary: list[Creature]
    machine_assignments: list[MachineAssignment]
    job_assignments: list[JobAssignment]
    dungeon_assignment: Optional[DungeonAssignment]
    expedition_assignments: list[ExpeditionAssignment]
    unassigned: list[Creature]
