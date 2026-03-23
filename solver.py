from itertools import combinations
from models import (
    Creature, Expedition, ExpeditionTier, JobAssignment, ExpeditionAssignment, SolverResult, JOBS
)
from calculator import xp_per_second, party_score, completion_time


def assign_jobs(creatures: list[Creature]) -> list[JobAssignment]:
    """
    Assign exactly one creature to each job.
    Rule: highest proficiency wins; tiebreak = highest level.
    """
    assignments = []
    assigned: set[str] = set()
    for job in JOBS:
        candidates = [c for c in creatures if c.name not in assigned]
        chosen = max(candidates, key=lambda c: (c.proficiency(job), c.level))
        assignments.append(JobAssignment(job=job, creature=chosen))
        assigned.add(chosen.name)
    return assignments


def _best_tier(party: list[Creature], expedition: Expedition) -> tuple[ExpeditionTier, float]:
    """Return (tier, xps) for the unlocked tier that maximises XP/s for this party."""
    return max(
        ((tier, xp_per_second(party, expedition, tier)) for tier in expedition.tiers),
        key=lambda x: x[1],
    )


def solve_expeditions(pool: list[Creature], expeditions: list[Expedition]) -> list[ExpeditionAssignment]:
    """
    Level-priority greedy solver:
      Process creatures from lowest level to highest. Each creature claims the best
      available (expedition, party, tier) that includes them. This ensures low-level
      creatures aren't crowded out of high-XP/s runs by high-stat creatures.
    """
    available: list[Creature] = sorted(pool, key=lambda c: c.level)
    avail_exps: list[Expedition] = list(expeditions)
    assignments: list[ExpeditionAssignment] = []

    while available and avail_exps:
        creature = available[0]
        others = available[1:]

        # Find the best (expedition, party) that includes `creature`.
        best_xps = -1.0
        best: tuple[Expedition, ExpeditionTier, list[Creature]] | None = None

        for exp in avail_exps:
            for extra in range(3):  # 0 companions, 1 companion, 2 companions
                if extra == 0:
                    party_options = [[creature]]
                else:
                    party_options = [
                        [creature] + list(comp)
                        for comp in combinations(others, extra)
                    ]
                for party in party_options:
                    tier, xps = _best_tier(party, exp)
                    if xps > best_xps:
                        best_xps = xps
                        best = (exp, tier, party)

        if best is None:
            break

        exp, tier, party = best
        ps = party_score(party, exp)
        t = completion_time(ps, tier.difficulty)
        assignments.append(ExpeditionAssignment(
            expedition=exp,
            tier=tier,
            party=party,
            xp_per_second=best_xps,
            time_minutes=t,
        ))
        for c in party:
            available.remove(c)
        avail_exps.remove(exp)

    return assignments


def solve(creatures: list[Creature], expeditions: list[Expedition]) -> SolverResult:
    job_assignments = assign_jobs(creatures)
    job_pool = {ja.creature.name for ja in job_assignments}

    expedition_pool = [c for c in creatures if c.name not in job_pool]
    expedition_assignments = solve_expeditions(expedition_pool, expeditions)

    assigned_to_exp = {c.name for ea in expedition_assignments for c in ea.party}
    unassigned = [c for c in expedition_pool if c.name not in assigned_to_exp]

    return SolverResult(
        job_assignments=job_assignments,
        expedition_assignments=expedition_assignments,
        unassigned=unassigned,
    )
