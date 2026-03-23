"""CLI entry point: run the solver and print results."""
from data_loader import load_creatures, load_expeditions
from solver import solve
from calculator import creature_score, party_score


def main():
    """Load data, run solver, and print job/expedition/unassigned results."""
    creatures = load_creatures()
    expeditions = load_expeditions()
    result = solve(creatures, expeditions)

    print("=" * 52)
    print("JOB ASSIGNMENTS")
    print("=" * 52)
    for ja in result.job_assignments:
        c = ja.creature
        prof = c.proficiency(ja.job)
        print(f"  {ja.job:<12} -> {c.name:<10} Lv{c.level:<3} (proficiency {prof})")

    print()
    print("=" * 52)
    print("EXPEDITION ASSIGNMENTS")
    print("=" * 52)
    for ea in result.expedition_assignments:
        t = ea.tier
        ps = party_score(ea.party, ea.expedition)
        print(f"\n  {ea.expedition.name}")
        print(f"  Tier {t.number}  diff={t.difficulty}  xp_reward={t.xp_reward}")
        print(f"  Party score: {ps}  |  Time: {ea.time_minutes:.1f} min"
              f"  |  XP/s: {ea.xp_per_second:.4f}")
        for c in ea.party:
            score = creature_score(c, ea.expedition)
            print(f"    -{c.name:<10} Lv{c.level:<3} {c.type:<6} [{c.trait}]  score={score}")

    if result.unassigned:
        print()
        print("=" * 52)
        print("UNASSIGNED (no expedition slot)")
        print("=" * 52)
        for c in result.unassigned:
            print(f"  {c.name:<10} Lv{c.level:<3} {c.type} [{c.trait}]")


if __name__ == "__main__":
    main()
