# Circular Organics Planner

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Open%20Planner-23865B?style=for-the-badge)](https://circular-organics-planner.streamlit.app/)
[![Tests](https://img.shields.io/badge/tests-23%20passing-2C9A69?style=flat-square)](tests/test_engine.py)
[![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=flat-square)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Deployed-FF4B4B?style=flat-square)](https://streamlit.io/)

## From NSW food-waste rules to a building-level operating plan.

**Circular Organics Planner** helps managers of shared food buildings decide between **Off-site FOGO, Hybrid and On-site processing** — then turns that decision into an actionable plan with waste allocation, bins, collections, trade-offs and a roadmap to 2035.

Built for **Climate Hack-tion 2026 — Build for 2035**  
Challenge area: **Zero Waste & Methane Reduction**

### [Open the live planner →](https://circular-organics-planner.streamlit.app/)

> Planning guidance only. Final compliance, equipment and site decisions should be checked against current NSW EPA guidance, council requirements and site-specific conditions.

---

## The decision gap

NSW can tell a food business **when food waste needs to be separated**.

But a facility manager still has to decide:

**Off-site FOGO? Hybrid? On-site processing?**

And that decision immediately creates more questions:

- How much food waste should stay on site?
- How much still needs external collection?
- How many bins are required?
- How often should they be collected?
- What does each option cost operationally?
- Which option performs better environmentally?
- What conditions would justify changing the setup later?
- Will today's decision still make sense in 2035?

The problem is not simply getting another food-waste bin.

It is turning **policy + waste volume + space + budget + operational constraints** into a setup that can actually work.

**Circular Organics Planner fills the planning gap between policy guidance and vendor procurement.**

---

## One input flow. One operating plan.

```text
Building inputs
      ↓
Waste stream profile
      ↓
NSW mandate check
      ↓
3-pathway simulation
      ↓
Transparent recommendation
      ↓
Implementation plan
      ↓
Trade-off analysis
      ↓
Next decision point
      ↓
2035 roadmap
      ↓
Evidence & sources
```

The planner returns:

- likely NSW FOGO timing
- recommended pathway
- on-site and off-site waste allocation
- required FOGO bins
- collection frequency and days
- bin lifts per week
- indicative collection cost
- landfill methane avoided
- modelled net GHG impact
- recommendation reasons
- comparison with the main alternative
- practical implementation steps
- the next decision point toward 2035
- assumptions, ranges, confidence levels and source links

---

# Demo result — 1,000 kg/week food court

Our main demo is an illustrative shopping-centre food court generating **1,000 kg of food waste per week**.

The site has:

- 10 m² available for on-site processing
- a potential local use for processed material
- a Medium equipment budget
- 5% expected annual food-waste growth

The planner recommends:

## **HYBRID**

| Decision | Result |
|---|---|
| **Recommended pathway** | **Hybrid** |
| NSW status | Likely covered now |
| Generated food waste | 1,000 kg/week |
| Captured food waste | 700 kg/week |
| Processed on site | **350 kg/week** |
| Sent off site | **350 kg/week** |
| FOGO setup | **2 × 240 L bins** |
| Collections | **4/week** |
| Bin lifts | **8/week** |
| Landfill methane avoided | **1,911 kg CH₄/year** base |
| Hybrid net GHG saving | ~**37 t CO₂e/year** |

### Why Hybrid?

Compared with sending the captured food waste entirely through Off-site FOGO:

**Hybrid uses 8 fewer bin lifts per week.**

```text
Off-site FOGO     16 lifts/week
Hybrid             8 lifts/week
                  ──────────────
Difference          8 fewer
```

The model also estimates approximately:

**$270.81/week lower indicative collection cost**

for the Hybrid collection setup.

But the planner deliberately shows the downside too:

> **Climate trade-off:** Off-site FOGO has the higher modelled net GHG saving in this example — approximately **46 vs 37 t CO₂e/year**.

The recommended pathway does not have to win every metric.

That is the point.

Circular Organics Planner is a **decision-support tool**, not a single-metric optimiser.

---

# Not a vendor calculator. Not a black box.

## It does not automatically prefer on-site processing

A smaller or constrained building can still receive **Off-site FOGO** as the recommendation.

On-site processing only becomes a candidate when the existing waste volume, space, budget and operational conditions support it.

---

## It compares before it recommends

The engine simulates all three pathways:

| | Off-site FOGO | Hybrid | On-site |
|---|---|---|---|
| External processing | High | Partial | Low |
| On-site processing | None | Partial | High |
| Space requirement | Low | Medium | High |
| Operational effort | Low | Medium | High |
| Equipment budget | Low | Medium | High |

The engine also calculates pathway-specific:

- waste allocation
- bins
- collections
- bin lifts
- floor-space requirement
- indicative collection cost
- equipment budget
- methane avoided
- net GHG impact

Only then is the recommendation shown.

---

## It uses explicit rules

The final pathway is selected by **six visible decision rules — R0 to R5**.

There is no hidden AI score.

Users can inspect:

- which rules fired
- why a pathway was recommended
- why another pathway was not selected
- what would need to change for the recommendation to change

---

## It shows trade-offs instead of hiding them

Operational convenience and climate impact do not always point to the same answer.

The planner keeps them visible separately.

For example, the main demo recommends Hybrid because it substantially reduces external bin handling and collection cost under the current planning assumptions.

At the same time, the app clearly shows that Off-site FOGO produces a higher modelled net GHG saving in that case.

---

# Build for 2035

The challenge is not only:

> **What should this building do today?**

It is also:

> **When should this building reconsider that decision?**

For the 1,000 kg/week demo:

```text
HYBRID TODAY
     │
     │ 5% annual food-waste growth
     ▼
~1,551 kg/week by 2035
     │
     ▼
1,500 kg/week volume threshold reached
     │
     ▼
ON-SITE can become a candidate
only if the other conditions are met
```

The planner does **not** say:

> 1,500 kg/week = automatically switch to On-site.

For full On-site processing, the current rule set also requires:

- at least **15 m²** of on-site space
- a **High** equipment budget
- the other pathway conditions to remain satisfied

The demo building currently has:

```text
Space       10 m²       → needs at least 15 m²
Budget      Medium      → needs High
```

So even though projected waste reaches roughly **1,551 kg/week by 2035**, the recommendation remains **Hybrid** if those other conditions do not change.

That makes the 2035 output a **decision point**, not just a growth chart.

---

# Evidence, not hidden constants

The application is built on a separate evidence and assumptions layer rather than burying planning numbers inside the UI.

## Current model

| Evidence layer | Current project |
|---|---:|
| Configurable assumption rows | **39** |
| Documented research sources | **23** |
| High-confidence values | **9** |
| Medium-confidence values | **10** |
| Low-confidence / team assumptions | **20** |
| Scenario values | **Min / Base / Max** |

Each assumption can include:

- minimum value
- base value
- maximum value
- unit
- source
- confidence classification
- notes

### Evidence classification

**H — High**

Directly supported for the stated scope.

**M — Medium**

Modelled, vendor-supplied or adapted evidence that still requires site-specific checks.

**L — Low**

A proposed planning assumption.

Low-confidence values are not hidden or presented as established facts.

They remain visible so they can later be replaced by measured site data or stronger evidence.

### Min / Base / Max are planning scenarios

They are **not statistical confidence intervals**.

They are used to show how different reasonable planning assumptions affect the output.

---

# Research foundation

The evidence layer covers:

### Food-waste generation

Illustrative waste-generation estimates for:

- cafes
- restaurants
- quick-service outlets
- bakeries
- grocery / food retail

Where measured waste data is available, it overrides the generic estimate.

A **7-day weighed waste audit** is preferred to relying on tenant-type defaults.

### Bin and collection planning

Research inputs include:

- food-waste density
- 240 L organics-bin capacity
- bin footprint
- fill ratio
- service-weight assumptions
- collection intervals
- collection frequency

### Emissions

The model keeps separate:

- landfill net GHG
- off-site processing GHG
- on-site processing GHG
- landfill fugitive methane

This is why:

**landfill methane avoided**

and

**net GHG saving**

are shown as separate outputs.

### Costs and operating assumptions

The planning model also includes:

- Sydney collection pricing
- indicative small-equipment budgets
- indicative larger-system budgets
- operating-cost assumptions
- labour
- electricity
- maintenance

These values are planning inputs, **not supplier quotes**.

### NSW policy

The research layer also covers:

- 2026 threshold
- 2028 threshold
- 2030 threshold
- mixed-bin configurations
- shared waste services
- relevant premises
- dining-area exemptions
- on-site pre-processing exemptions
- exemption expiry dates

The planner therefore reports mandate results as **likely**, not as a final legal determination.

---

# How the decision engine works

```text
INPUT
 │
 ▼
Waste Stream Profile
 │
 ▼
NSW Mandate Check
 │
 ▼
Off-site / Hybrid / On-site Simulation
 │
 ▼
R0–R5 Recommendation
 │
 ▼
Implementation Plan
 │
 ├──── Trade-off Analysis
 │
 ├──── Next Decision Point
 │
 └──── 2035 Roadmap
```

## Recommendation rules

| Rule | Condition | Result |
|---|---|---|
| **R0** | Default | Off-site FOGO |
| **R1** | On-site space under 6 m² | Hybrid and On-site excluded |
| **R2** | ≥500 kg/week + ≥6 m² + local-use condition + Medium/High budget | Hybrid candidate |
| **R3** | ≥1,500 kg/week + ≥15 m² + High budget | On-site candidate |
| **R4** | On-site is top candidate but no local-use condition | Return to Off-site FOGO |
| **R5** | Off-site requires high collection frequency and Hybrid reduces it | Advisory note |

The engine selects the highest pathway whose conditions are satisfied, then applies the remaining rule logic.

These thresholds are **planning rules**.

They are not:

- NSW legal thresholds
- guaranteed economic break-even points
- guarantees that a particular piece of equipment is appropriate

Site-specific checks are still required.

---

# From recommendation to implementation

The application does not stop after saying:

> **Choose Hybrid.**

It turns that recommendation into an operating plan.

For the selected pathway the engine calculates:

```text
Food waste captured
        ↓
On-site / off-site allocation
        ↓
Required bin capacity
        ↓
Collection schedule
        ↓
Bin lifts
        ↓
Indicative collection cost
        ↓
Climate impact
        ↓
Immediate next steps
```

The collection logic also considers the **longest gap between collection days**, not just average weekly capacity.

---

# Climate impact

## Landfill methane avoided

This estimates the methane associated with food waste that would otherwise go to landfill.

The model uses separate low, base and high planning cases.

For the main demo:

**1,911 kg CH₄/year avoided — base scenario**

---

## Net GHG saving

Net GHG includes the processing route as well.

This matters because on-site processing is not automatically the lowest-emission option.

For the main demo:

```text
Off-site FOGO     ≈ 46 t CO₂e/year saving
Hybrid            ≈ 37 t CO₂e/year saving
```

Hybrid still becomes the recommendation because the current rule set also considers operational feasibility.

The two metrics are deliberately kept separate.

---

# Validation

## 23 automated tests passing

The current test suite covers:

- R0–R5 recommendation behaviour
- NSW mandate threshold logic
- exact threshold boundaries
- mixed bin configurations
- tenant waste estimation
- measured-value overrides
- collection planning
- emissions cross-checks
- roadmap behaviour
- Case 1 regression
- Case 2 regression
- trade-off delta calculations
- next-decision-point constraints
- evidence-summary calculations

### Case 1 regression

**Small café building**

```text
Recommendation       Off-site FOGO
FOGO bins            2 × 240 L
Collections          4/week
Methane avoided      669 kg CH₄/year base
```

### Case 2 regression

**Shopping-centre food court**

```text
Recommendation       Hybrid
On site              350 kg/week
Off site             350 kg/week
FOGO bins            2 × 240 L
Collections          4/week
Methane avoided      1,911 kg CH₄/year base
```

Automated tests validate the behaviour and consistency of the implementation.

They do **not** replace real-world site validation.

---

# Try it

## Live application

### **https://circular-organics-planner.streamlit.app/**

For the clearest demo:

1. Open the live planner.
2. Load the **Shopping centre** example.
3. Run the comparison.
4. Review the **Hybrid** recommendation.
5. Check the operational **Trade-off**.
6. Check the **Build for 2035** decision point.
7. Open **Data & Sources** to inspect the model.

No installation is required.

---

# Who it is for

The current MVP is designed for **NSW buildings where multiple food businesses share a waste service**, such as:

- shopping-centre food courts
- university food precincts
- mixed food-retail buildings
- shared commercial food facilities

The main user is the:

**facility or building manager responsible for the shared waste service.**

The tool is intended to support the planning stage before committing to a supplier or equipment purchase.

---

# Important limitations

Circular Organics Planner is a **planning and decision-support tool**, not a compliance determination, engineering design or legal opinion.

Important limitations:

- NSW mandate results are shown as **likely** because not every exemption or site-specific condition is fully modelled.
- Tenant food-waste defaults are illustrative planning assumptions, not NSW industry averages.
- A measured waste audit should replace generic estimates wherever possible.
- Methane and GHG outputs are planning scenarios rather than statistical confidence intervals.
- Some modelled GHG scenarios may be negative.
- Cost estimates are indicative and do not replace supplier quotations.
- One public Sydney provider is used as a collection-price comparator, not as a full NSW market survey.
- On-site processing may require approvals, ventilation, fire-safety, trade-waste and other site checks.
- Rapidly processed or dehydrated food waste is not automatically usable compost.
- A local-use input does not prove that a particular reuse pathway is legally or technically suitable.
- Equipment footprint assumptions do not represent a full site engineering assessment.
- The 2035 roadmap changes waste volume while keeping most other site conditions constant.
- Current exemptions and regulatory requirements should be checked again before implementation.

The limitations are intentionally visible because an explainable recommendation should show what it **does not know**, not only what it calculates.

---

# Tech stack

## Application

- **Python**
- **Streamlit**
- **pandas**
- **Altair**

## Testing

- **pytest**

## Deployment

- **GitHub**
- **Streamlit Community Cloud**

## Design and collaboration

- **Figma**
- **Google Docs**
- **Google Sheets**
- **Google Drive**

The production recommendation is generated by the Python rule engine.

**AI is not the recommendation engine.**

---

# Project structure

```text
circular-organics-planner/
│
├── app/
│   ├── main.py
│   └── engine.py
│
├── data/
│   ├── assumptions.csv
│   ├── examples.json
│   └── example_outputs.json
│
├── docs/
│   └── SPEC.md
│
├── tests/
│   └── test_engine.py
│
├── requirements.txt
├── README.md
└── .gitignore
```

### `app/main.py`

Streamlit application and final product interface.

### `app/engine.py`

Core planning and decision engine.

### `data/assumptions.csv`

Configurable planning values, ranges, confidence levels and evidence references.

### `data/examples.json`

Fixed illustrative demonstration inputs.

### `data/example_outputs.json`

Regression and frontend reference outputs.

### `docs/SPEC.md`

Engine contract, rule definitions and implementation decisions.

### `tests/test_engine.py`

Automated acceptance and regression tests.

---

# Run locally

Clone:

```bash
git clone https://github.com/alexcho121/circular-organics-planner.git
cd circular-organics-planner
```

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
streamlit run app/main.py
```

Run tests:

```bash
pytest -q
```

Current result:

```text
23 passed
```

---

# Data and source approach

The research foundation draws primarily from:

- NSW EPA FOGO mandate and rollout guidance
- NSW EPA business food-waste guidance
- NSW EPA organics-processing technology assessment
- NSW EPA exemption guidance and Gazette notices
- NSW Government waste-capacity guidance
- Australian DCCEEW waste-policy material
- UNFCCC material
- Global Methane Pledge material
- Australian equipment specifications
- Sydney collection-service pricing used for indicative planning

The project research pack documents **23 sources**.

The application configuration uses selected values from that research together with clearly labelled team planning assumptions.

Model values and evidence links can be inspected in:

[`data/assumptions.csv`](data/assumptions.csv)

The engine contract and rules are documented in:

[`docs/SPEC.md`](docs/SPEC.md)

Vendor sources are used only for indicative sizing, operating inputs or pricing.

They are not presented as NSW Government requirements or endorsements.

---

# Third-party tools and AI disclosure

The project used:

- Python
- Streamlit
- pandas
- Altair
- pytest
- GitHub
- Streamlit Community Cloud
- Figma
- Google Docs / Sheets / Drive

AI tools including **Claude and OpenAI ChatGPT/Codex** were used to assist with activities such as drafting, development support, debugging and review.

Team members reviewed, modified and tested the final project outputs.

**The pathway recommendation itself is not generated by an AI model.**

It comes from the transparent **R0–R5 Python decision engine**.

---

# Team

| Member | Contribution |
|---|---|
| **Yuna Kim** | **Project coordination, decision rules, QA, submission** |
| **Jongyoon Yoo** | **Figma design, demo script, video, QA** |
| **Youngjun Cho** | **Full-stack app development, decision engine, UI implementation, deployment** |
| **Yeonsu Kim** | **Research, evidence, assumptions and modelling data** |

---

# Hackathon

**Climate Hack-tion 2026**  
**Build for 2035 — Zero Waste & Methane Reduction**

Circular Organics Planner turns policy, evidence and operational constraints into an explainable building-level plan.

**Not just whether food waste should be separated — but how the building can actually do it.**
