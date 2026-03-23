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

**Job assignment (pre-solve step):**
- 6 jobs: Chopping, Mining, Exploring, Digging, Fishing, Farming
- Exactly 1 creature assigned per job; a creature can only hold 1 job
- For each job: pick creature with highest proficiency (0–10); tiebreak = lowest level
- Job-assigned creatures are removed from the expedition pool before solving

**Expedition tiers:**
- `xp_reward: null` in a tier means that difficulty is not yet unlocked — skip in solver
- Party size is 1–3 creatures; smaller parties are valid when fewer creatures remain

## Data
- 20 expeditions, 5 difficulty tiers each
- 4 types: water, fire, earth, wind
- 13+ traits
- 6 stats: POW, GRT, AGI, SMT, LOT, LCK
- 6 jobs: Chopping, Mining, Exploring, Digging, Fishing, Farming (proficiency 0–10)

## Planned Architecture
koltera_solver/
├── data/
│   ├── creatures.json      # Your creature roster
│   └── expeditions.json    # All 20 expeditions
├── models.py               # Dataclasses: Creature, Expedition, Assignment
├── calculator.py           # Score, time, XP/s computations
├── objective.py            # Pluggable objective functions
├── solver.py               # Optimization algorithms
├── data_loader.py          # JSON I/O, validation
└── main.py                 # CLI: run solver, print results

## Solver Objectives & Constraints
- Goal: level ALL creatures — every creature should be assigned to either a job or an expedition slot
- Unassigned creatures are acceptable only if total slots (6 jobs + expeditions×3) < creature count
- xp_reward scales with difficulty (Water Delivery: xp = 270 + 1.8×difficulty); stored explicitly per tier in JSON