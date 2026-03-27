"""Job and expedition assignment solver."""
from collections import defaultdict
from itertools import combinations
from statistics import pstdev
from models import (
    Creature, Expedition, ExpeditionTier, JobAssignment, ExpeditionAssignment, SolverResult, JOBS
)
from calculator import xp_per_second, party_score, completion_time


_max_sanctuary = 8


def _best_combo_by_proficiency(
    group: list[Creature], selected: list[Creature], slots: int
) -> tuple[Creature, ...]:
    """Return the combo of `slots` creatures from `group` minimising job proficiency std dev."""
    best: tuple[Creature, ...] = ()
    best_std = float("inf")
    for combo in combinations(group, slots):
        job_sums = [sum(c.proficiency(j) for c in selected + list(combo)) for j in JOBS]
        std = pstdev(job_sums)
        if std < best_std:
            best_std = std
            best = combo
    return best


def assign_sanctuary(creatures: list[Creature]) -> list[Creature]:
    """
    Select up to 8 awakened creatures for the Sanctuary.
    Priority: highest tier first. When a tier must be split to fill the last slots,
    choose the subset that minimises std dev of summed job proficiencies across the party.
    """
    awakened = [c for c in creatures if c.awakening > 0]
    if len(awakened) <= _max_sanctuary:
        return awakened

    by_tier: dict[int, list[Creature]] = defaultdict(list)
    for c in awakened:
        by_tier[c.tier].append(c)

    selected: list[Creature] = []
    for tier in sorted(by_tier.keys(), reverse=True):
        group = by_tier[tier]
        slots_left = _max_sanctuary - len(selected)
        if len(group) <= slots_left:
            selected.extend(group)
        else:
            selected.extend(_best_combo_by_proficiency(group, selected, slots_left))
            break
        if len(selected) == _max_sanctuary:
            break

    return selected


def assign_jobs(creatures: list[Creature]) -> list[JobAssignment]:
    """
    Assign exactly one creature to each job.
    Rule: highest proficiency wins; tiebreak = highest level.
    """
    assignments = []
    assigned: set[str] = set()
    for job in JOBS:
        candidates = [c for c in creatures if c.name not in assigned]
        chosen = max(candidates, key=lambda c, j=job: (c.proficiency(j), c.awakening, c.level))
        assignments.append(JobAssignment(job=job, creature=chosen))
        assigned.add(chosen.name)
    return assignments


def _best_tier(party: list[Creature], expedition: Expedition) -> tuple[ExpeditionTier, float]:
    """Return (tier, xps) for the unlocked tier that maximises XP/s for this party."""
    return max(
        ((tier, xp_per_second(party, expedition, tier)) for tier in expedition.tiers),
        key=lambda x: x[1],
    )


def _find_best_for_creature(
    creature: Creature,
    others: list[Creature],
    avail_exps: list[Expedition],
) -> tuple[Expedition, ExpeditionTier, list[Creature], float] | None:
    """Return (expedition, tier, party, xps) maximising XP/s with creature in the party."""
    best_xps = -1.0
    best: tuple[Expedition, ExpeditionTier, list[Creature], float] | None = None
    for exp in avail_exps:
        for extra in range(3):  # 0 companions, 1 companion, 2 companions
            party_options = (
                [[creature]]
                if extra == 0
                else [[creature] + list(comp) for comp in combinations(others, extra)]
            )
            for party in party_options:
                tier, xps = _best_tier(party, exp)
                if xps > best_xps:
                    best_xps = xps
                    best = (exp, tier, party, xps)
    return best


def solve_expeditions(
    pool: list[Creature], expeditions: list[Expedition]
) -> list[ExpeditionAssignment]:
    """
    Level-priority greedy solver:
      Process creatures from lowest level to highest. Each creature claims the best
      available (expedition, party, tier) that includes them. This ensures low-level
      creatures aren't crowded out of high-XP/s runs by high-stat creatures.
    """
    available: list[Creature] = sorted(pool, key=lambda c: (c.awakening, c.level))
    avail_exps: list[Expedition] = list(expeditions)
    assignments: list[ExpeditionAssignment] = []

    while available and avail_exps:
        creature = available[0]
        best = _find_best_for_creature(creature, available[1:], avail_exps)
        if best is None:
            break
        exp, tier, party, best_xps = best
        ps = party_score(party, exp)
        assignments.append(ExpeditionAssignment(
            expedition=exp,
            tier=tier,
            party=party,
            xp_per_second=best_xps,
            time_minutes=completion_time(ps, tier.difficulty),
        ))
        for c in party:
            available.remove(c)
        avail_exps.remove(exp)

    return assignments


def solve(creatures: list[Creature], expeditions: list[Expedition]) -> SolverResult:
    """Run sanctuary assignment, then job assignment, then expedition assignment."""
    sanctuary = assign_sanctuary(creatures)
    sanctuary_names = {c.name for c in sanctuary}

    remaining = [c for c in creatures if c.name not in sanctuary_names]

    job_assignments = assign_jobs(remaining)
    job_pool = {ja.creature.name for ja in job_assignments}

    expedition_pool = [c for c in remaining if c.name not in job_pool]
    expedition_assignments = solve_expeditions(expedition_pool, expeditions)

    assigned_to_exp = {c.name for ea in expedition_assignments for c in ea.party}
    unassigned = [c for c in expedition_pool if c.name not in assigned_to_exp]

    return SolverResult(
        sanctuary=sanctuary,
        job_assignments=job_assignments,
        expedition_assignments=expedition_assignments,
        unassigned=unassigned,
    )
