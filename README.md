# Koltera 2 Expedition Solver

Optimally assigns creatures to expeditions and jobs in Koltera 2, maximising XP/s across your entire roster so every creature levels up.

## What it does

- Assigns one creature per job (Chopping, Mining, Exploring, Digging, Fishing, Farming) based on proficiency
- Assigns remaining creatures to expeditions in parties of up to 3, picking the best tier and party composition per expedition
- Maximises XP per second, accounting for type bonuses, trait bonuses, stat weights, and party score

## Setup

1. Copy `data/creature_levels.json.example` to `data/creature_levels.json` and set each creature's current level
2. Copy `data/expedition_progress.json.example` to `data/expedition_progress.json` and set how many tiers you have unlocked per expedition (0 = not unlocked)

> `creature_levels.json` and `expedition_progress.json` are personal save data and are gitignored.

## Usage

```
python main.py
```

Output shows job assignments, then each expedition with its party, score, time, and XP/s.

## Data files

| File | What it contains | Gitignored |
|------|-----------------|------------|
| `data/creatures.json` | Creature roster: stats, types, traits, job proficiencies | No |
| `data/expeditions.json` | All known expeditions: types, traits, weights, tier difficulties/rewards | No |
| `data/creature_levels.json` | Your creatures' current levels | Yes |
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