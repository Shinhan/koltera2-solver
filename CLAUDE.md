# Koltera 2 Expedition Solver

## Confirmed Game Mechanics

**Score formula:**
`floor(floor(base_score) × type_mult × trait_mult)`
- base_score = Σ(stat × weight)
- preferred_type: ×1.5, opposing_type: ×0.5, preferred_trait: ×1.5
- Multipliers apply sequentially on the floored base (type first, then trait)
- Party score = sum of individual creature scores

**Stat scaling:**
`stat = base_stat × level`

**Time formula:**
`time_minutes = max(5.0, 60 - 55 × party_score / difficulty)`
- Game *displays* floor(time) but uses exact float for XP/s

**XP/s formula:**
`xp_per_second = xp_reward / (party_size × time_minutes × 60)`

**Awakening:**
- A creature at max level can be "Awakened": resets level to 0, enables Sanctuary placement
- Tracked in `creature_levels.json` as `"awakening": int` (0 = not awakened)
- Moss (tier 0 in-game) is displayed as tier 0 but treated as tier 1 by the solver — leave as-is

**Job assignment (first step):**
- 6 jobs: Chopping, Mining, Exploring, Digging, Fishing, Farming
- Exactly 1 creature assigned per job; a creature can only hold 1 job
- For each job: pick creature with highest proficiency (0–10); tiebreak = highest awakening, then highest level
- Job-assigned creatures are removed from all subsequent pools

**Sanctuary (post-job step):**
- Only awakened creatures are eligible
- At most 8 creatures; selected by descending tier
- If a tier must be split to fill the last slots, choose the subset minimising std dev of summed job proficiencies across the party
- Sanctuary creatures are removed from the machine/expedition pool before solving

**Machine assignment (optional, `--machine` flag, post-job step):**
- 9 machines with fixed element requirements:
  - Bakery (water), Sawmill (wind), Greenhouse (earth), Smelter (fire), Cooker (fire)
  - Stone Quarry, Stick Finder, Coal Miner, Refinery (any element)
- Only awakened creatures are eligible
- Type-specific slots are filled first, then any-type slots
- Tiebreak: highest awakening, then highest level
- Machine-assigned creatures are removed from the expedition pool before solving

**Expedition solver priority:**
- Process creatures in order: non-awakened first, then awakened; within each group, lowest level first
- Ensures non-awakened creatures (who can't go to Sanctuary) are never crowded out by awakened ones
- `--awakened-helpers` flag: restricts expedition party helpers (companions) to awakened creatures only; the primary creature being assigned is unrestricted

**Expedition tiers:**
- `xp_reward: null` in a tier means that difficulty is not yet unlocked — skip in solver
- Party size is 1–3 creatures; smaller parties are valid when fewer creatures remain

## Data
- 20 expeditions, 5 difficulty tiers each
- 4 types: water, fire, earth, wind
- 13 traits
- 6 stats: POW, GRT, AGI, SMT, LOT, LCK
- 6 jobs: Chopping, Mining, Exploring, Digging, Fishing, Farming (proficiency 0–10)

## Architecture
```
├── data/
│   ├── creatures.json           # Your creature roster
│   ├── creature_levels.json     # Current level + awakening per creature (gitignored)
│   ├── expeditions.json         # All 20 expeditions
│   └── expedition_progress.json # Unlocked tier count per expedition (gitignored)
├── models.py               # Dataclasses: Creature, Expedition, Assignment, MachineAssignment
├── calculator.py           # Score, time, XP/s computations
├── solver.py               # Optimization algorithms
├── data_loader.py          # JSON I/O, validation
└── main.py                 # CLI: run solver, print results
```

## Solver Objectives & Constraints
- Goal: level ALL creatures — every creature should be assigned to sanctuary, a job, a machine, or an expedition slot
- Unassigned creatures are acceptable only if total slots (8 sanctuary + 6 jobs + 9 machines + expeditions×3) < creature count
- xp_reward scales with difficulty (Water Delivery: xp = 270 + 1.8×difficulty); stored explicitly per tier in JSON