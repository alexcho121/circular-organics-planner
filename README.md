# Circular Organics Planner

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Open%20Planner-23865B?style=for-the-badge)](https://circular-organics-planner.streamlit.app/)
[![Tests](https://img.shields.io/badge/tests-23%20passing-2C9A69?style=flat-square)](tests/test_engine.py)

**From NSW food-waste rules to a building-level operating plan.**

Circular Organics Planner helps managers of shared food buildings compare **Off-site FOGO, Hybrid and On-site processing**, then turns that decision into a practical plan: waste allocation, bins, collections, trade-offs and the next decision point on the way to 2035.

Built for **Climate Hack-tion 2026 — Build for 2035**  
Challenge area: **Zero Waste & Methane Reduction**

### [Open the live planner →](https://circular-organics-planner.streamlit.app/)

---

## The decision nobody gives building managers

NSW can tell a food business **when food waste needs to be separated**.

But a facility manager still has to decide:

- Off-site FOGO, Hybrid or On-site processing?
- How much waste should stay on site?
- How many bins are needed?
- How often should they be collected?
- What are the operational and climate trade-offs?
- When should the building reconsider that choice as it grows?

The problem is not simply getting another bin.

It is turning policy, waste volume, space, budget and operational constraints into a setup that can actually work.

**Circular Organics Planner fills the gap between policy guidance and vendor procurement.**

---

## One input flow. One operating plan.

```text
Building inputs
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
- indicative collection cost
- landfill methane avoided
- modelled net GHG impact
- recommendation reasons
- trade-offs against the main alternative
- next decision point toward 2035
- assumptions, ranges and source links

---

# Demo result — 1,000 kg/week food court

Our main demo is an illustrative shopping-centre food court generating **1,000 kg of food waste per week**, with 10 m² of on-site processing space, a local use for processed material and a Medium equipment budget.

| Decision | Result |
|---|---|
| **Recommended pathway** | **Hybrid** |
| NSW status | Likely covered now |
| Captured food waste | 700 kg/week |
| Processed on site | **350 kg/week** |
| Sent off site | **350 kg/week** |
| FOGO setup | **2 × 240 L bins** |
| Collections | **4/week** |
| Bin lifts | **8/week** |
| Landfill methane avoided | **1,911 kg CH₄/year** base |
| Hybrid net GHG saving | ~**37 t CO₂e/year** |

### Why Hybrid?

Compared with Off-site FOGO, the Hybrid setup gives this building:

- **8 fewer bin lifts per week**
- about **$270.81/week lower indicative collection cost**
- a local use for part of the processed output

But the planner does **not** hide the downside.

> **Climate trade-off:** Off-site FOGO has the higher modelled net GHG saving in this example — approximately **46 vs 37 t CO₂e/year**.

That is intentional.

The planner is not trying to make one pathway win every metric. It helps the manager see the operational and environmental trade-offs before making a decision.

---

## Why this is different

### It does not automatically prefer on-site processing

A small or constrained building can still receive **Off-site FOGO** as the recommendation.

On-site processing only becomes a candidate when the existing volume, space, budget and operational conditions support it.

### It is not a black-box recommendation

The planner uses **six explicit decision rules — R0 to R5**.

The user can inspect:

- which rules fired
- why the selected pathway was recommended
- why another pathway was not selected
- what would need to change for the recommendation to change

### It compares before it recommends

All three pathways are simulated before the final plan is shown.

The comparison includes:

- on-site / off-site kg
- bins
- collections
- bin lifts
- indicative collection cost
- space
- operational effort
- equipment budget
- methane avoided
- net GHG impact

### It shows trade-offs instead of hiding them

The recommended pathway does not have to be best on every metric.

That is important for real facility decisions.

### It looks beyond today

The planner identifies the **next decision point** rather than producing only a one-time answer.

---

# Build for 2035

The challenge is not only deciding what works today.

It is understanding **when the building should reconsider that decision**.

For the 1,000 kg/week demo building:

```text
HYBRID TODAY
     │
     │ 5% annual food-waste growth
     ▼
~1,551 kg/week by 2035
     │
     ▼
1,500 kg/week volume threshold crossed
     │
     ▼
ON-SITE becomes a candidate only if
other conditions are also satisfied
```

Crossing the volume threshold does **not** automatically change the recommendation.

Under the current Case 2 conditions, On-site would still require:

- at least **15 m² of on-site space**
- a **High** equipment budget
- the other existing pathway conditions to remain satisfied

The current site has only 10 m² and a Medium budget, so the planner continues to show **Hybrid** under those unchanged conditions.

This makes the roadmap a decision tool rather than a simple growth chart.

---

# Evidence, not hidden assumptions

The model is intentionally inspectable.

| Evidence | Current model |
|---|---:|
| Assumption rows | **39** |
| Unique source IDs directly linked from `assumptions.csv` | **11** |
| High-confidence assumptions | **9** |
| Medium-confidence assumptions | **10** |
| Low-confidence / team assumptions | **20** |
| Full project research set | **23 references** |

Each assumption can include:

- minimum value
- base value
- maximum value
- unit
- source ID
- source URL
- confidence level
- notes

The app exposes these values through **Data & Sources** rather than hiding them inside the code.

Government and public-sector sources are preferred where suitable. Vendor sources are used for indicative equipment sizing and pricing only, not as NSW Government requirements or endorsements.

Team assumptions are explicitly identified.

> Where measured site data exists, it should replace generic estimates. A weighed food-waste audit is more reliable than estimating waste from tenant type.

---

# How the decision engine works

```text
Input
  │
  ▼
Waste Stream Profile
  │
  ▼
NSW Mandate Check
  │
  ▼
Off-site ─ Hybrid ─ On-site
      scenario simulation
  │
  ▼
R0–R5 Recommendation
  │
  ▼
Implementation Plan
  │
  ├── Trade-off Analysis
  │
  ├── Next Decision Point
  │
  └── 2035 Roadmap
```

The final pathway decision is **rule-based**, not generated by an AI model.

### Recommendation rules

| Rule | Condition | Result |
|---|---|---|
| **R0** | Default | Off-site FOGO |
| **R1** | On-site space under 6 m² | Hybrid and On-site excluded |
| **R2** | ≥500 kg/week, ≥6 m², local use, Medium/High budget | Hybrid candidate |
| **R3** | ≥1,500 kg/week, ≥15 m², High budget | On-site candidate |
| **R4** | On-site candidate but no local use | Return to Off-site FOGO |
| **R5** | Off-site requires high collection frequency and Hybrid reduces it | Advisory note |

The planner selects the highest pathway whose conditions are satisfied and then applies the remaining rules.

These thresholds are **planning rules**, not laws or guaranteed economic break-even points.

Numeric assumptions and thresholds are kept in the project data layer rather than scattered through the UI.

---

# Implementation planning

The recommendation is converted into a practical operating plan.

For each pathway the engine calculates:

- captured food waste
- kg processed on site
- kg sent off site
- required FOGO bins
- collections per week
- collection days
- bin lifts per week
- bin footprint
- indicative collection cost
- landfill methane avoided
- net GHG saving

The collection planner also considers the longest gap between services rather than only dividing total weekly waste by bin capacity.

---

# Climate impact

The planner deliberately separates two climate metrics.

### Landfill methane avoided

Shows the estimated methane avoided by keeping captured food waste out of landfill.

Because the same captured food waste is diverted in all three scenarios, methane avoided can be similar across pathways.

### Net GHG saving

Accounts for the modelled emissions associated with the processing pathway itself.

That means one pathway can reduce operational collection pressure while another has a better modelled GHG result.

The tool shows both.

Ranges are **planning scenarios**, not statistical confidence intervals.

---

# Validation

The current engine has:

## **23 automated tests passing**

They cover:

- R0–R5 recommendation behaviour
- NSW mandate thresholds
- exact boundary cases
- tenant waste estimation
- measured-value overrides
- collection planning
- 2035 roadmap behaviour
- worked emissions cross-check
- Case 1 regression
- Case 2 regression
- signed trade-off calculations
- next-decision-point constraints
- evidence-summary calculations

### Case 1

Small café building:

- **Off-site FOGO**
- 2 × 240 L bins
- 4 collections/week
- **669 kg CH₄/year** base landfill methane avoided

### Case 2

Shopping-centre food court:

- **Hybrid**
- 350 kg/week on site
- 350 kg/week off site
- 2 × 240 L bins
- 4 collections/week
- **1,911 kg CH₄/year** base landfill methane avoided

Automated tests validate the software behaviour and internal model consistency. They are not a substitute for real-world pilot validation.

---

# Try it

## Live application

### https://circular-organics-planner.streamlit.app/

For the clearest demonstration:

1. Open the planner.
2. Load the **Shopping centre** example.
3. Run **Compare pathways**.
4. Review the Hybrid recommendation.
5. Check the Trade-off section.
6. Check the Build for 2035 decision point.
7. Open Data & Sources to inspect the assumptions.

No installation is required.

---

# Who it is for

The current MVP focuses on **NSW buildings where multiple food businesses share a waste service**, including:

- shopping-centre food courts
- university food precincts
- mixed food-retail buildings
- shared commercial food facilities

The main user is the **facility or building manager responsible for the shared waste service**.

The planner is intended to support the stage before a manager requests vendor quotes or commits to equipment.

---

# Important limitations

Circular Organics Planner is a **planning and decision-support tool**, not a compliance determination, engineering design or legal opinion.

Important limitations include:

- NSW mandate results are shown as **likely** because not every exemption or site-specific condition is modelled.
- Tenant food-waste defaults are illustrative planning assumptions, not NSW averages.
- A measured waste audit should replace estimated volumes wherever possible.
- Methane and GHG outputs are scenario estimates, not statistical confidence intervals.
- Some modelled GHG ranges can be negative.
- Costs are indicative and should not replace supplier quotes.
- On-site equipment requires site-specific checks including approvals, ventilation, fire safety and trade-waste requirements.
- Processed food waste is not automatically usable compost.
- Space assumptions do not represent a full engineering site assessment.
- The 2035 roadmap changes waste volume while most other site conditions remain fixed.

These limitations are exposed deliberately so users can understand what the model can and cannot conclude.

---

# Tech stack

### Application

- **Python**
- **Streamlit**
- **pandas**
- **Altair**

### Validation

- **pytest**

### Deployment and collaboration

- **GitHub**
- **Streamlit Community Cloud**

The final pathway decision uses the transparent Python rule engine rather than an AI recommendation model.

---

# Project structure

```text
circular-organics-planner/
│
├── app/
│   ├── main.py              # Streamlit application
│   └── engine.py            # Decision and planning engine
│
├── data/
│   ├── assumptions.csv      # Model values, ranges, sources and confidence
│   ├── examples.json        # Demo building inputs
│   └── example_outputs.json # Regression/demo outputs
│
├── docs/
│   └── SPEC.md              # Engine contract and decision rules
│
├── tests/
│   └── test_engine.py       # Automated engine tests
│
├── requirements.txt
├── README.md
└── .gitignore
```

The project keeps the application interface, decision engine, assumptions/evidence and validation tests separated.

---

# Run locally

Clone the repository:

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

Run the application:

```bash
streamlit run app/main.py
```

Run the tests:

```bash
pytest -q
```

Current result:

```text
23 passed
```

---

# Data and source approach

The planner draws primarily on:

- NSW EPA FOGO mandate and rollout guidance
- NSW EPA business food-waste guidance
- NSW EPA organics-processing assessments
- NSW EPA mandate exemptions
- Australian DCCEEW waste-policy material
- UNFCCC material
- Global Methane Pledge material
- equipment and collection-provider specifications for indicative sizing and pricing

The model values and direct source links can be inspected in:

[`data/assumptions.csv`](data/assumptions.csv)

The engine and output contract are documented in:

[`docs/SPEC.md`](docs/SPEC.md)

Vendor sources are used for indicative planning only and do not represent NSW Government requirements or endorsements.

---

# Third-party tools and AI disclosure

Development and collaboration tools used during the hackathon included:

- Python
- Streamlit
- pandas
- Altair
- pytest
- GitHub
- Streamlit Community Cloud
- Figma
- Google Docs / Sheets / Drive

AI tools were used to assist with drafting, coding, debugging and review during development.

The team reviewed, modified and tested the final implementation.

**AI is not used to choose the final food-waste pathway.**  
The recommendation itself is produced by the transparent R0–R5 Python decision engine.

---

# Team

| Member | Role |
|---|---|
| **Yuna Kim** | Lead, recommendation rules, testing and submission |
| **Jongyoon Yoo** | App design, Demo video and presentation support |
| **Youngjun Cho** | Full application development, decision engine, frontend/UI, design implementation, README and deployment |
| **Yeonsu Kim** | Research and evidence lead — NSW policy research, assumptions dataset, source verification, emissions/cost factors and modelling inputs |

---

# Hackathon

**Climate Hack-tion 2026**  
**Build for 2035 — Zero Waste & Methane Reduction**

Circular Organics Planner explores how policy, waste data and operational constraints can be turned into an explainable building-level decision tool — not just another waste calculator.
