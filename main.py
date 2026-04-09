"""CLI entry point: run the solver and print results."""
import argparse
from data_loader import load_creatures, load_expeditions
from models import DUNGEON_TYPES, DungeonAssignment, JOBS
from solver import solve

_SEP = "=" * 52


def _print_dungeon(da: DungeonAssignment) -> None:
    print(_SEP)
    print(f"DUNGEON ({da.dungeon_type.upper()})  -  party score: {da.party_score}")
    print(_SEP)
    print("  Party: " + ", ".join(c.name for c in da.party))
    is_combat = da.dungeon_type == "combat"
    header = "  Tier     Diff  Grade   XP rate"
    if is_combat:
        header += "   Runes"
    print(header)
    for tr in da.tier_results:
        row = (
            f"  {tr.tier_number:<6} {tr.difficulty:>6}  {tr.grade:<5} {tr.xp_rate:>8.2f}"
        )
        if is_combat:
            row += f"  {tr.chronicle_runes:>6}"
        print(row)
    print()


def main():
    """Load data, run solver, and print job/expedition/unassigned results."""
    parser = argparse.ArgumentParser(description="Koltera expedition solver")
    parser.add_argument(
        "--min-party-size", type=int, default=1, choices=[1, 2, 3],
        metavar="{1,2,3}",
        help="Minimum creatures per expedition party (default: 1)",
    )
    parser.add_argument(
        "--machine", action="store_true",
        help="Assign awakened creatures to machines before expeditions",
    )
    parser.add_argument(
        "--awakened-helpers", action="store_true",
        help="Only awakened creatures may serve as expedition party helpers",
    )
    parser.add_argument(
        "--dungeon", choices=DUNGEON_TYPES,
        metavar="{" + ",".join(DUNGEON_TYPES) + "}",
        help=(
            "Pull 3 creatures for a dungeon first "
            "(combat: POW/GRT/AGI/SMT; others: SMT/LOT/LCK)"
        ),
    )
    parser.add_argument(
        "--fill-expeditions", action="store_true",
        help=(
            "Scale min party size by roster size and enforce it dynamically "
            "to guarantee no unassigned creatures (40-59 available: min 2; "
            "60+: min 3; dynamic floor = ceil(remaining/expeditions))"
        ),
    )
    args = parser.parse_args()

    creatures = load_creatures()
    expeditions = load_expeditions()
    result = solve(
        creatures, expeditions,
        min_party_size=args.min_party_size,
        use_machines=args.machine,
        awakened_helpers=args.awakened_helpers,
        dungeon_type=args.dungeon,
        fill_expeditions=args.fill_expeditions,
    )

    if result.dungeon_assignment:
        _print_dungeon(result.dungeon_assignment)

    print(_SEP)
    print("SANCTUARY")
    print(_SEP)
    job_sums = {
        job: sum(c.proficiency(job) for c in result.sanctuary) for job in JOBS
    }
    for c in result.sanctuary:
        print(f"  {c.name:<10} T{c.tier}  Lv{c.level:<3} (awakening {c.awakening})")
    totals = "  ".join(f"{j[:3]}:{v}" for j, v in job_sums.items())
    print("  Job proficiency totals: " + totals)

    print()
    print(_SEP)
    print("JOB ASSIGNMENTS")
    print(_SEP)
    for ja in result.job_assignments:
        c = ja.creature
        prof = c.proficiency(ja.job)
        print(f"  {ja.job:<12} -> {c.name:<10} Lv{c.level:<3} (proficiency {prof})")

    if result.machine_assignments:
        print()
        print(_SEP)
        print("MACHINE ASSIGNMENTS")
        print(_SEP)
        for ma in result.machine_assignments:
            c = ma.creature
            print(
                f"  {ma.machine:<14} -> {c.name:<10} T{c.tier}  Lv{c.level:<3}"
                f" (awakening {c.awakening}  {c.type})"
            )

    print()
    print(_SEP)
    print("EXPEDITION ASSIGNMENTS")
    print(_SEP)
    for ea in result.expedition_assignments:
        names = ", ".join(c.name for c in ea.party)
        print(f"\n  {ea.expedition.name}  Tier {ea.tier.number}  |  XP/s: {ea.xp_per_second:.4f}")
        print(f"    {names}")

    if result.unassigned:
        print()
        print(_SEP)
        print("UNASSIGNED (no expedition slot)")
        print(_SEP)
        for c in result.unassigned:
            print(f"  {c.name:<10} Lv{c.level:<3} {c.type} [{c.trait}]")


if __name__ == "__main__":
    main()
