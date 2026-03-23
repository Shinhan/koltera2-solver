from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

STATS = ["POW", "GRT", "AGI", "SMT", "LOT", "LCK"]
JOBS = ["Chopping", "Mining", "Exploring", "Digging", "Fishing", "Farming"]


@dataclass
class Creature:
    name: str
    tier: int
    type: str
    trait: str
    level: int
    base_stats: dict[str, int]
    job_proficiencies: dict[str, Optional[int]]

    @property
    def stats(self) -> dict[str, int]:
        return {s: self.base_stats[s] * self.level for s in STATS}

    def proficiency(self, job: str) -> int:
        return self.job_proficiencies.get(job) or 0


@dataclass
class ExpeditionTier:
    number: int       # 1-based original position in JSON
    difficulty: int
    xp_reward: int


@dataclass
class Expedition:
    name: str
    preferred_types: list[str]
    opposing_types: list[str]
    preferred_trait: str
    stat_weights: dict[str, float]
    tiers: list[ExpeditionTier]   # only unlocked tiers


@dataclass
class JobAssignment:
    job: str
    creature: Creature


@dataclass
class ExpeditionAssignment:
    expedition: Expedition
    tier: ExpeditionTier
    party: list[Creature]
    xp_per_second: float
    time_minutes: float


@dataclass
class SolverResult:
    job_assignments: list[JobAssignment]
    expedition_assignments: list[ExpeditionAssignment]
    unassigned: list[Creature]
