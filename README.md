# Koltera 2 Expedition Solver

Optimally assigns creatures to expeditions and jobs in Koltera 2, maximising XP/s across your entire roster so every creature levels up.

## What it does

1. **Jobs** — assigns one creature per job (Chopping, Mining, Exploring, Digging, Fishing, Farming) based on proficiency
2. **Sanctuary** — assigns awakened creatures (up to 8) from the remaining pool, prioritising highest tier
3. **Machines** *(optional, `--machine`)* — assigns awakened creatures to 9 machines: Bakery (water), Sawmill (wind), Greenhouse (earth), Smelter (fire), Cooker (fire), and Stone Quarry, Stick Finder, Coal Miner, Refinery (any element)
4. **Dungeon** *(optional, `--dungeon TYPE`)* — pulls 3 creatures for the dungeon before expeditions, selected by highest dungeon score
5. **Expeditions** — assigns remaining creatures to expeditions in parties of up to 3, picking the best tier and party composition — non-awakened creatures take priority over awakened ones
- Maximises XP per second, accounting for type bonuses, trait bonuses, stat weights, and party score

## Setup

1. Copy `data/creature_levels.json.example` to `data/creature_levels.json` and set each creature's current level and awakening (0 or 1)
2. Copy `data/expedition_progress.json.example` to `data/expedition_progress.json` and set how many tiers you have unlocked per expedition (0 = not unlocked)

> `creature_levels.json` and `expedition_progress.json` are personal save data and are gitignored.

## Usage

```
python main.py [--machine] [--min-party-size {1,2,3}] [--awakened-helpers] [--dungeon TYPE]
```

| Flag | Description |
|------|-------------|
| `--machine` | Assign awakened creatures to machines after jobs, before expeditions |
| `--min-party-size N` | Minimum creatures per expedition party (default: 1) |
| `--awakened-helpers` | Only awakened creatures may serve as party helpers (companions) in expeditions |
| `--dungeon TYPE` | Pull 3 creatures for a dungeon before expeditions. TYPE is one of: `combat`, `chopping`, `mining`, `digging`, `farming`, `fishing`, `exploring` |

Output shows Sanctuary, Job assignments, Machine assignments (if `--machine`), Dungeon assignment (if `--dungeon`), Expedition assignments, and any unassigned creatures.

## Dungeon mechanics

- **Combat** dungeons score on POW + GRT + AGI + SMT; all other types score on SMT + LOT + LCK
- 5 difficulty tiers: 2000 / 4000 / 6000 / 8000 / 10000
- Grade is determined by score vs. difficulty: S (≥2×), A (≥1×), B (≥0.6×), C (≥0.25×), F (<0.25×)
- Grade multipliers: S=×2, A=×1.5, B=×1, C=×0.5, F=×0.25 — applied to base XP rate and Chronicle Rune count
- Chronicle Runes (combat only): `max(1, floor(tier × 2 × grade_mult))` per tier

## Data files

| File | What it contains | Gitignored |
|------|-----------------|------------|
| `data/creatures.json` | Creature roster: stats, types, traits, job proficiencies | No |
| `data/expeditions.json` | All known expeditions: types, traits, weights, tier difficulties/rewards | No |
| `data/creature_levels.json` | Your creatures' current levels and awakening status | Yes |
| `data/expedition_progress.json` | How many tiers you have unlocked per expedition (0–5) | Yes |

## Contributing expedition data

`expeditions.json` and `creatures.json` are community data. If you have unlocked creatures or expeditions not yet in the file, please open a PR with data about them.

## Score formula

```
base_score   = Σ(stat × weight),  where stat = base_stat × level
type_score   = floor(base_score) × 1.5  (preferred type) or × 0.5  (opposing type)
final_score  = floor(type_score) × 1.5  (if preferred trait matches)
party_score  = sum of individual scores
time_minutes = max(5.0, 60 − 55 × party_score / difficulty)
xp_per_second = xp_reward / (party_size × time_minutes × 60)
```

## License

[GPL-3.0](LICENSE)