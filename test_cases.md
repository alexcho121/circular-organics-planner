# Test cases (spec v1)

Run `python -m pytest -q` from the repository root: 23 tests pass. The table lists the 17 original v1 acceptance tests; the suite also checks the trade-off deltas, the next decision point (two tests), the evidence summary and both demo snapshots. Boundaries are inclusive (W = T1 counts as reaching T1). Unless stated: no local use, Low budget, 0 m² on-site space, waste room 10 m².

| ID | Case | Input (key values) | Expected result |
|---|---|---|---|
| T01 | Small building, no on-site space | 150 kg/week; general waste 3 × 240 L × 2/week (1,440 L) | Off-site FOGO (R0, R1); mandate "Likely covered from 1 July 2030" |
| T02 | Large building, space Limited | 2,000 kg/week; 2 m²; local use; High budget; 6 × 660 L × 3/week | Off-site FOGO (R1 wins); "Likely covered now" |
| T03 | Medium volume, Moderate space, local use, Medium budget | 800 kg/week; 8 m²; local use; Medium budget; 10 × 240 L × 2/week (4,800 L) | Hybrid (R2); "Likely covered now" |
| T04 | Large volume, Ample space, High budget | 2,000 kg/week; 20 m²; local use; High budget | On-site (R2, R3) + regulatory and safety warning |
| T11 | Large volume, Ample space, only a Medium budget | 2,000 kg/week; 20 m²; local use; Medium budget | Hybrid (R2); next step names a High budget for On-site |
| T12 | Hybrid conditions met except the budget | 800 kg/week; 8 m²; local use; Low budget | Off-site FOGO (R0); next step names a Medium budget for a small unit |
| T05 | On-site conditions met, no local use | 2,000 kg/week; 20 m²; no local use; High budget | Off-site FOGO (R3, R4); "Secure a use for processed material…" |
| T06 | Exactly at T1 and the Moderate minimum | 500 kg/week; 6 m²; local use; Medium budget | Hybrid (R2) |
| T07 | Collections frequent (R5 note) | 1,200 kg/week; 8 m²; no local use; waste room 2 m² | Off-site FOGO at 7 collections/week; R5 note "Hybrid could cut this to about 4 per week…" |
| T08 | Mandate boundaries | 16 × 240 L × 1 = 3,840 L · 15 × 240 L = 3,600 L · 6 × 660 L = 3,960 L · 1 × 660 L · 2 × 240 L = 480 L | Covered now · from 2028 · covered now · from 2030 (single 660 L bin) · below thresholds |
| T09 | Roadmap with 10% growth a year | 400 kg/week; 8 m²; local use; Medium budget | 2026 Off-site · 2028 Off-site · 2030 Hybrid · 2035 Hybrid |
| T10 | Tenant estimate | 2 medium cafes + 1 large restaurant + bakery measured at 80 kg | W = 680 kg/week (measured kg is not multiplied by a size factor) |
| X1 | Research cross-check | W = 600 kg/week | Net GHG saving: Hybrid 0.432 t CO2e/week, Off-site 0.535 t CO2e/week (matches the research doc) |
