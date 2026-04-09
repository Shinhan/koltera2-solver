"""Job and expedition assignment solver."""
from collections import defaultdict
from itertools import combinations
from math import ceil
from statistics import pstdev
from models import (
    Creature, Expedition, ExpeditionTier, JobAssignment, MachineAssignment,
    ExpeditionAssignment, DungeonAssignment, SolverResult, JOBS,
)
from calculator import (
    xp_per_second, party_score, completion_time,
    creature_dungeon_score, dungeon_tier_results,
)


_MAX_SANCTUARY = 8


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
    if len(awakened) <= _MAX_SANCTUARY:
        return awakened

    by_tier: dict[int, list[Creature]] = defaultdict(list)
    for c in awakened:
        by_tier[c.tier].append(c)

    selected: list[Creature] = []
    for tier in sorted(by_tier.keys(), reverse=True):
        group = by_tier[tier]
        slots_left = _MAX_SANCTUARY - len(selected)
        if len(group) <= slots_left:
            selected.extend(group)
        else:
            selected.extend(_best_combo_by_proficiency(group, selected, slots_left))
            break
        if len(selected) == _MAX_SANCTUARY:
            break

    return selected


_MACHINES: list[tuple[str, str | None]] = [
    ("Stone Quarry", None),
    ("Stick Finder", None),
    ("Coal Miner",   None),
    ("Smelter",      "fire"),
    ("Sawmill",      "wind"),
    ("Cooker",       "fire"),
    ("Greenhouse",   "earth"),
    ("Bakery",       "water"),
    ("Refinery",     None),
]


def assign_machines(creatures: list[Creature]) -> list[MachineAssignment]:
    """
    Assign awakened creatures to machines.
    Type-specific slots (water/wind/earth/fire) are filled first, then any-type slots.
    Within each pass: prefer highest awakening, then highest level.
    Only awakened creatures are eligible.
    """
    awakened = [c for c in creatures if c.awakening > 0]
    assigned: set[str] = set()
    assignments: list[MachineAssignment] = []

    def _key(c: Creature) -> tuple[int, int]:
        return (c.awakening, c.level)

    for machine_name, required_type in _MACHINES:
        if required_type is not None:
            candidates = [c for c in awakened if c.type == required_type and c.name not in assigned]
        else:
            candidates = [c for c in awakened if c.name not in assigned]
        if not candidates:
            continue
        chosen = max(candidates, key=_key)
        assignments.append(MachineAssignment(machine=machine_name, creature=chosen))
        assigned.add(chosen.name)

    return assignments


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
    min_party_size: int = 1,
    awakened_helpers: bool = False,
) -> tuple[Expedition, ExpeditionTier, list[Creature], float] | None:
    """Return (expedition, tier, party, xps) maximising XP/s with creature in the party."""
    helpers = [c for c in others if c.awakening > 0] if awakened_helpers else others
    best_xps = -1.0
    best: tuple[Expedition, ExpeditionTier, list[Creature], float] | None = None
    # extra = number of companions; party size = 1 + extra (max 3)
    min_extra = max(0, min_party_size - 1)
    for exp in avail_exps:
        for extra in range(min_extra, 3):  # companions: 0, 1, or 2
            if extra == 0:
                party_options = [[creature]]
            else:
                if len(helpers) < extra:
                    continue
                party_options = [[creature] + list(comp) for comp in combinations(helpers, extra)]
            for party in party_options:
                tier, xps = _best_tier(party, exp)
                if xps > best_xps:
                    best_xps = xps
                    best = (exp, tier, party, xps)
    return best


def solve_expeditions(
    pool: list[Creature],
    expeditions: list[Expedition],
    min_party_size: int = 1,
    awakened_helpers: bool = False,
    fill: bool = False,
) -> list[ExpeditionAssignment]:
    """
    Level-priority greedy solver:
      Process creatures from lowest level to highest. Each creature claims the best
      available (expedition, party, tier) that includes them. This ensures low-level
      creatures aren't crowded out of high-XP/s runs by high-stat creatures.

    With fill=True: base min_party_size scales with pool size (40-59 -> 2, 60+ -> 3),
    and each iteration dynamically raises the minimum to ceil(remaining/expeditions)
    so that all creatures are guaranteed a slot when the pool started below 60.
    """
    available: list[Creature] = sorted(pool, key=lambda c: (c.awakening, c.level))
    avail_exps: list[Expedition] = list(expeditions)
    assignments: list[ExpeditionAssignment] = []

    n = len(available)
    if fill:
        base_min = 3 if n >= 60 else 2 if n >= 40 else 1
    else:
        base_min = min_party_size

    while available and avail_exps:
        if fill:
            needed = ceil(len(available) / len(avail_exps))
            effective_min = min(max(base_min, needed), 3)
        else:
            effective_min = base_min
        creature = available[0]
        best = _find_best_for_creature(
            creature, available[1:], avail_exps, effective_min, awakened_helpers
        )
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


def assign_dungeon(creatures: list[Creature], dungeon_type: str) -> DungeonAssignment:
    """
    Select the 3 creatures with the highest dungeon score for the dungeon.
    Combat: equal weights on POW, GRT, AGI, SMT.
    Other types: equal weights on SMT, LOT, LCK.
    """
    ranked = sorted(creatures, key=lambda c: creature_dungeon_score(c, dungeon_type), reverse=True)
    party = ranked[:3]
    score = sum(creature_dungeon_score(c, dungeon_type) for c in party)
    return DungeonAssignment(
        dungeon_type=dungeon_type,
        party=party,
        party_score=score,
        tier_results=dungeon_tier_results(score, dungeon_type),
    )


def _exclude(pool: list[Creature], names: set[str]) -> list[Creature]:
    return [c for c in pool if c.name not in names]


def solve(
    creatures: list[Creature],
    expeditions: list[Expedition],
    min_party_size: int = 1,
    use_machines: bool = False,
    awakened_helpers: bool = False,
    dungeon_type: str | None = None,
    fill_expeditions: bool = False,
) -> SolverResult:
    """Run optional dungeon, job, sanctuary, optional machine, and expedition assignments."""
    dungeon_assignment: DungeonAssignment | None = None
    if dungeon_type is not None:
        dungeon_assignment = assign_dungeon(creatures, dungeon_type)
        creatures = _exclude(creatures, {c.name for c in dungeon_assignment.party})

    job_assignments = assign_jobs(creatures)
    remaining = _exclude(creatures, {ja.creature.name for ja in job_assignments})

    sanctuary = assign_sanctuary(remaining)
    remaining = _exclude(remaining, {c.name for c in sanctuary})

    machine_assignments: list[MachineAssignment] = []
    if use_machines:
        machine_assignments = assign_machines(remaining)
        remaining = _exclude(remaining, {ma.creature.name for ma in machine_assignments})

    expedition_assignments = solve_expeditions(
        remaining, expeditions, min_party_size, awakened_helpers, fill=fill_expeditions
    )
    assigned_to_exp = {c.name for ea in expedition_assignments for c in ea.party}

    return SolverResult(
        sanctuary=sanctuary,
        machine_assignments=machine_assignments,
        job_assignments=job_assignments,
        dungeon_assignment=dungeon_assignment,
        expedition_assignments=expedition_assignments,
        unassigned=_exclude(remaining, assigned_to_exp),
    )
