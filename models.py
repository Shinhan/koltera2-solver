"""Data model dataclasses for creatures, expeditions, and solver results."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

STATS = ["POW", "GRT", "AGI", "SMT", "LOT", "LCK"]
JOBS = ["Chopping", "Mining", "Exploring", "Digging", "Fishing", "Farming"]


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
class SolverResult:
    """Complete solver output: sanctuary, job assignments, expedition assignments, and leftovers."""
    sanctuary: list[Creature]
    job_assignments: list[JobAssignment]
    expedition_assignments: list[ExpeditionAssignment]
    unassigned: list[Creature]
