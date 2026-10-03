# Circular Organics Planner: build handoff (spec v1)

For Yeongjun, from 19:00 Sat 3 Oct. Everything here runs today: `pytest -q` gives 17 passed.
Status: **approved by Yuna, Sat 3 Oct 16:15 (spec v1 frozen).** Changes after the freeze go through Yuna and the Decision Log.

## 0. Approved decisions (applied in this pack)

1. **T1 = 500 kg/week, T2 = 1,500 kg/week** (Yeonsu's base values).
2. **Space:** the form asks for on-site space in m². Under 6 m² = Limited, 6 to under 15 m² = Moderate, 15 m² or more = Ample.
3. **Budget select:** Low = under $30,000 (no equipment), Medium = $30,000 to $100,000 (small unit), High = $100,000 or more (larger system). To match these ranges, Hybrid now needs a Medium or High budget (R2) and On-site needs a High budget (R3).
4. **Mandate check** uses the EPA branches. All bins 240 L: 3,840 L/week (2026) and 1,920 (2028). Any other mix: 3,960 and 1,980. From 2030: 720 L/week, or any single bin of 660 L or more. The status says "Likely covered…" and always shows an exemptions note, because the tool does not model exemptions.
5. **Two climate numbers:** landfill methane avoided (kg CH4/year) and net GHG saving (t CO2e/year, can be negative). Methane avoided is the same for every pathway because diversion is the same. Net GHG differs by pathway.
6. **Collection plan:** pick the least frequent schedule whose longest gap is 2 days or less (4 a week: Mon, Wed, Fri, Sun). Bins = ceil(off-site kg × gap ÷ 7 ÷ bin mass). Bin mass = min(240 × 0.514 × 0.45, 60, 96) = 55.5 kg. If the bins do not fit the waste room, collect more often.
7. **R4:** On-site candidate but no local use → Off-site FOGO. **R5:** note only. It shows when Off-site needs 5 or more collections a week and Hybrid would need fewer.
8. **Should items:** indicative collection cost from Sydney price per bin lift (ex GST) and equipment budget ranges (not quotes).

## 1. Files

| File | What it is |
|---|---|
| `SPEC.md` | This page |
| `assumptions.csv` | Every number the app uses (39 rows: key, min/base/max, unit, source, confidence). Change numbers here, never in code |
| `engine.py` | Reference engine: pure Python, no UI. Use it as is, port it, or check your own code against it |
| `test_engine.py` | 17 acceptance tests (`pytest -q`) |
| `test_cases.md` | The same tests in plain words |
| `examples.json` | Inputs for the two demo buildings |
| `example_outputs.json` | Full outputs for both demo buildings; the frontend can build against these tonight |

## 2. How to plug it in (Q2: pick one)

- **Streamlit:** `from engine import load_config, plan_building`, then `result = plan_building(inputs, load_config())`, then render.
- **Web frontend + API:** one endpoint, `POST /api/plan`. Body = input JSON (section 3), response = output JSON (section 4). Until the API is up, the frontend uses `example_outputs.json` as mock data.

## 3. Input contract

| Field | Type | Form label | Required | Notes |
|---|---|---|---|---|
| `building_name` | text | Plan page title | No | |
| `building_type` | shopping_centre, food_court, university, commercial_building, hospitality | Building type | Yes | Display only |
| `total_food_waste_kg_week` | number | Total food waste (kg/week) | This or `tenants` | Overrides tenants |
| `tenants` | list of {name, type, size, count, kg_week?} | Enter by tenant | This or the total | type: cafe, restaurant, quick_service, bakery, grocery. size: small, medium, large. A measured kg_week overrides the default |
| `current_collections_per_week` | integer | Current collections per week | Yes | Organics only; 0 allowed |
| `general_waste_bins` | list of {size_l, count, collections_per_week} | **New:** General waste bins | Yes | General waste only, not recycling |
| `waste_room_area_m2` | number | Waste room area (m²) | Yes | |
| `onsite_space_m2` | number | Space for on-site processing (m²) | Yes | 0 if none |
| `local_use` | true/false | Local use for processed material? | Yes | |
| `budget_level` | low, medium, high | **New:** Budget for on-site equipment | Yes | Labels in `budget_labels` |
| `current_collection_cost_aud_week` | number | Current collection cost (optional) | No | Shown beside the indicative cost |
| `annual_change_pct` | number | **New:** Expected change in food waste per year (%) | No (default 0) | Roadmap only |

## 4. Output contract

- `waste_profile`: `total_kg_week`, `source` (entered or estimated), `tenants[]`
- `mandate`: `capacity_l_week`, `branch`, `status_code` (covered_2026, from_2028, from_2030, below, unknown), `status_text`, `start_year`, `threshold_l_week`, `notes[3]`
- `recommendation`: `pathway` (offsite, hybrid, onsite), `label`, `space_band`, `rules_fired`, `reasons[≤3]`, `rejected`, `warnings[]`, `what_would_change`, `r5_note`
- `comparison.offsite | hybrid | onsite`: `offsite_kg_week`, `onsite_kg_week`, `bins`, `bin_size_l`, `collections_per_week`, `collection_days`, `lifts_per_week`, `room_ok`, `collection_cost_aud_week`, `diverted_kg_week`, `diverted_kg_year`, `ch4_avoided_kg_year{low,base,high}`, `net_ghg_t_year{low,base,high}`, `space`/`cost`/`effort` (Low, Medium, High), `equipment_budget`
- `plan`: the chosen pathway's comparison fields + `collections_change`, `next_steps[3]`, `local_use_line`
- `roadmap`: `rows[]` for 2026, 2028, 2030 and 2035 (`year`, `food_waste_kg_week`, `mandate`, `pathway`, `next_step`, `action`), `cumulative_net_ghg_t_2026_2035{low,base,high}`, `note`
- `budget_labels{low,medium,high}`

Figma mapping: the Compare page rows read from `comparison`. "Methane avoided (range)" becomes two rows: `ch4_avoided_kg_year` and `net_ghg_t_year`. The Plan page reads `plan` and `roadmap`. The mandate banner reads `mandate`.

## 5. Logic

**C0 mandate check:** capacity = Σ(bin size L × count × collections per week), general waste bins only. Thresholds as in decision 4.

| Rule | Condition | Result |
|---|---|---|
| R0 | Default | Off-site FOGO |
| R1 | On-site space under 6 m² (Limited) | Exclude Hybrid and On-site |
| R2 | W ≥ 500 and space ≥ 6 m² and local use and budget Medium or High | Hybrid candidate |
| R3 | W ≥ 1,500 and space ≥ 15 m² and budget High | On-site candidate + safety warning |
| R4 | On-site is the top candidate but no local use | Off-site FOGO + "Secure a use for processed material…" |
| R5 | Result Off-site, R1 not fired, Off-site needs ≥ 5 collections/week and Hybrid fewer | Note only |

Pick the highest candidate (On-site > Hybrid > Off-site), then apply R4. `what_would_change` lists the unmet conditions of the next pathway up.

**Plan:** captured = W × 0.7. On-site share: Off-site 0, Hybrid 0.5, On-site 0.9. Off-site kg = captured − on-site kg. Bins and schedule as in decision 6. Cost = bin lifts × price per lift for that frequency.

**Impact (per year):** net GHG = (captured × 1.296 − off-site × 0.0222 − on-site × 0.5116) ÷ 1000 × 52 (t CO2e). Landfill methane avoided = captured t × 52.5 × 52 (kg CH4). Low uses min capture, min landfill and max processing factors; high uses the reverse.

**Roadmap:** each year W_y = W × (1 + g)^(y − 2026); bin capacity scales the same way; other inputs stay constant. Re-run C0 and R0 to R5. The fixed action text per year comes from the research doc.

## 6. Demo buildings (illustrative data)

| | Case 1: small cafe building | Case 2: shopping centre food court |
|---|---|---|
| Tenants | 3 medium cafes + 1 small bakery = 350 kg/week | 3 restaurants + 2 quick service + 1 cafe = 1,000 kg/week |
| General waste | 4 × 240 L × 2/week = 1,920 L | 6 × 660 L × 3/week = 11,880 L |
| Mandate | Likely covered from 1 July 2028 | Likely covered now |
| Space, use, budget | 0 m², no local use, Low | 10 m², local use, Medium |
| Recommendation | Off-site FOGO | Hybrid |
| Plan | 2 × 240 L bins, Mon/Wed/Fri/Sun, 8 lifts (about $271/week) | 2 × 240 L bins, 8 lifts (Off-site would need 16, about $542/week) |
| Landfill methane avoided | 669 kg CH4/year (218 to 1,228) | 1,911 kg CH4/year (624 to 3,510) |
| Net GHG saving | 16 t CO2e/year (4 to 33) | Hybrid 37 t (−2 to 93); Off-site 46 t |
| Roadmap | Off-site throughout; Hybrid needs 500 kg, 6 m², a local use and a Medium budget | At 5% a year: 1,551 kg/week by 2035; On-site then needs 15 m² and a High budget |

Honest point for the pitch: in Case 2, off-site composting saves slightly more net GHG than Hybrid. Hybrid is recommended because it halves bin lifts and uses the output locally. The tool shows both numbers.

## 7. Still open

- Q2: which stack, and who builds the frontend
- Yeonsu to confirm: the mixed-bin branch (3,960 / 1,980 L) and the single 660 L bin rule for 2030
- Q6: deadline time zone; Q7: deploy a live link
