"""CLI entry point: run the solver and print results."""
from data_loader import load_creatures, load_expeditions
from solver import solve


def main():
    """Load data, run solver, and print job/expedition/unassigned results."""
    creatures = load_creatures()
    expeditions = load_expeditions()
    result = solve(creatures, expeditions)

    print("=" * 52)
    print("SANCTUARY")
    print("=" * 52)
    job_sums = {job: sum(c.proficiency(job) for c in result.sanctuary) for job in ["Chopping", "Mining", "Exploring", "Digging", "Fishing", "Farming"]}
    for c in result.sanctuary:
        print(f"  {c.name:<10} T{c.tier}  Lv{c.level:<3} (awakening {c.awakening})")
    print(f"  Job proficiency totals: " + "  ".join(f"{j[:3]}:{v}" for j, v in job_sums.items()))

    print()
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
        names = ", ".join(c.name for c in ea.party)
        print(f"\n  {ea.expedition.name}  Tier {ea.tier.number}  |  XP/s: {ea.xp_per_second:.4f}")
        print(f"    {names}")

    if result.unassigned:
        print()
        print("=" * 52)
        print("UNASSIGNED (no expedition slot)")
        print("=" * 52)
        for c in result.unassigned:
            print(f"  {c.name:<10} Lv{c.level:<3} {c.type} [{c.trait}]")


if __name__ == "__main__":
    main()
