# Circular Organics Planner

**A practical decision tool for food-waste planning in NSW shared food buildings.**

Circular Organics Planner compares three food-waste pathways — **Off-site FOGO, Hybrid, and On-site processing** — and recommends a practical setup based on waste volume, available space, local reuse, budget, and NSW food-organics requirements.

Built for **Climate Hack-tion 2026 — Build for 2035**, Zero Waste & Methane Reduction.

> Planning guidance only. Final compliance, equipment and site decisions should be checked against current NSW EPA guidance, council requirements and site-specific conditions.

---

## The problem

Food waste sent to landfill produces methane, but choosing an alternative is not as simple as selecting the option with the lowest emissions.

A building manager may need to consider:

- whether the site is likely covered by NSW food-organics requirements
- how much food waste the building generates
- available bin and processing space
- collection frequency
- whether processed material can be used locally
- budget and operational effort
- how the building may change by 2035

Existing guidance provides the rules and data, but turning them into a practical site plan can still take time.

**Circular Organics Planner turns those inputs into a clear recommendation and implementation plan.**

---

## What the planner does

The app guides the user through five questions:

1. **Is the site likely covered by the NSW food-organics mandate?**
2. **Which of the three pathways fits the building?**
3. **Why is that pathway recommended?**
4. **What should the building actually do?**
5. **Will that recommendation still make sense by 2035?**

The three pathways are:

| Pathway | Description |
|---|---|
| **Off-site FOGO** | Separate food waste and send it to an external organics processor. |
| **Hybrid** | Process part of the food waste on site and send the remainder off site. |
| **On-site** | Process most food waste on site, subject to space, budget, reuse and site requirements. |

The goal is not simply to maximise on-site processing.

**Most of the methane benefit comes from keeping food waste out of landfill. The pathway decision is about finding a setup that can realistically work for the building.**

---

## What the user gets

After entering a small set of building and waste inputs, the planner returns:

- recommended pathway
- NSW mandate status
- on-site and off-site waste allocation
- required FOGO bins
- collection frequency
- estimated landfill methane avoided
- estimated net GHG impact
- recommendation reasons
- implementation steps
- 2035 outlook

Detailed assumptions, sources and technical comparisons are available when the user wants to inspect them.

---

## Who it is for

The current MVP is designed for **NSW buildings where several food businesses share a waste service**, such as:

- shopping-centre food courts
- university food precincts
- mixed food retail buildings
- other shared commercial food facilities

The main user is the **building or facility manager responsible for the shared waste service**.

---

## How it works

The planner uses a transparent rule-based decision engine rather than a black-box AI recommendation.

```text
Building & waste inputs
        ↓
Waste stream profile
        ↓
NSW mandate check
        ↓
Off-site / Hybrid / On-site comparison
        ↓
Recommendation
        ↓
Implementation plan
        ↓
2035 projection
```

Recommendation thresholds and model assumptions are stored outside the core logic in the project data files.

This makes the recommendation easier to explain, inspect and update when better data becomes available.

---

## Example outcomes

### Small food building

A small building with limited space and no local use for processed material is likely to remain better suited to **Off-site FOGO**.

### Larger food court

A larger food court with sufficient waste volume, some processing space and a local use for output may be better suited to a **Hybrid** model.

In the project example, the Hybrid pathway reduces external bin lifts while still diverting the full food-waste stream from landfill.

The app also shows cases where the pathway with the highest modelled GHG saving is not necessarily the recommended operational pathway. The purpose of the tool is to make those trade-offs visible rather than hide them.

---

## Built for 2035

The planner does not only evaluate today's setup.

It can project food-waste growth and show whether the recommended pathway remains suitable as the site approaches **2035**.

This helps building managers see whether their current plan is:

- likely to remain suitable
- approaching a Hybrid transition point
- approaching the space and budget requirements for full On-site processing

The roadmap is intentionally simple and is designed for early planning rather than long-term forecasting.

---

## Transparent assumptions

The model keeps assumptions separate from the recommendation code.

The project data includes:

- minimum, base and maximum values
- source links where available
- confidence levels
- team assumptions clearly identified as assumptions

Examples include:

- food-waste estimates
- FOGO bin capacity
- collection cost
- methane factors
- GHG factors
- processing capacity
- space requirements
- budget ranges

Where measured site data is available, it should replace generic estimates.

For example, a **seven-day weighed food-waste audit** is more reliable than estimating waste from tenant type.

---

## Important limitations

This is a **planning tool, not a compliance determination**.

Important limitations include:

- NSW mandate results are shown as **likely** because exemptions and every site-specific condition are not fully modelled.
- Tenant food-waste estimates are planning assumptions, not NSW averages.
- Methane and GHG outputs are scenario estimates rather than statistical confidence intervals.
- On-site processing still requires site-specific checks for approvals, ventilation, fire safety, trade waste and equipment suitability.
- Processed food waste is not automatically usable compost.
- Cost estimates are indicative and should not replace supplier quotes.
- Space requirements are planning estimates and may not include all equipment clearance, storage or ventilation requirements.
- The 2035 projection changes waste volume while keeping most other assumptions constant.

The app exposes these assumptions so that users can understand where the recommendation comes from.

---

## Tech stack

- **Python**
- **Streamlit**
- **pandas**
- **Altair**
- **pytest**
- **GitHub**

The MVP uses a transparent rule-based engine rather than an AI model for the final pathway decision.

---

## Run locally

Clone the repository:

```bash
git clone https://github.com/alexcho121/circular-organics-planner.git
cd circular-organics-planner
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
streamlit run app/main.py
```

---

## Project structure

```text
circular-organics-planner/
│
├── app/
│   ├── main.py
│   └── engine.py
│
├── data/
│   └── ...
│
├── tests/
│   └── ...
│
├── README.md
├── requirements.txt
└── .gitignore
```

The final structure may be adjusted during the hackathon cleanup, but the project maintains a separation between:

- application UI
- decision engine
- model assumptions and evidence
- tests

---

## Evidence and sources

The planner is based primarily on NSW and Australian government guidance, environmental assessments and equipment specifications.

Key source groups include:

- NSW EPA — FOGO mandates and rollout
- NSW EPA — business food-waste guidance
- NSW EPA — organics-processing technology assessment
- NSW EPA — mandate exemptions
- Australian DCCEEW — food waste and National Waste Policy
- UNFCCC — COP31
- Global Methane Pledge
- equipment and collection supplier specifications used only for indicative sizing and pricing

The complete assumption list, source URLs and confidence ratings are maintained with the project data and are also accessible through the app's **Methodology & evidence** section.

Vendor sources are used for indicative sizing and pricing only and do not represent NSW Government requirements or endorsements.

---

## Team

| Member | Role |
|---|---|
| **Yuna Kim** | Lead, recommendation rules, testing and submission |
| **Jongyoon Yoo** | UI/design, demo and README |
| **Yeongjun Cho** | Decision engine and application |
| **Yeonsu Kim** | Research and data |

---

## Hackathon

**Climate Hack-tion 2026**  
**Challenge:** Build for 2035 — Zero Waste & Methane Reduction

The project was built as a hackathon MVP to demonstrate how existing policy, waste data and operational constraints can be turned into an explainable planning tool for building managers.
