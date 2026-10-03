"""Circular Organics Planner: Streamlit app (first version, spec v1).

Run from this folder:  streamlit run app.py
Flow follows the Figma design: 1 Input -> 2 Compare -> 3 Plan, plus Data & sources.
All numbers come from engine.py + assumptions.csv; nothing is hard-coded here.
"""
import json
import math
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from engine import (LABELS, PATHWAYS, budget_bands, load_config, plan_building,
                    recommend, v, waste_profile)

st.set_page_config(page_title="Circular Organics Planner", layout="wide")

HERE = Path(__file__).parent
CFG = load_config(HERE / "assumptions.csv")
EXAMPLES = json.loads((HERE / "examples.json").read_text(encoding="utf-8"))
BUDGET = budget_bands(CFG)

SERIES = "#2a78d6"      # categorical slot 1 (single series)
NEUTRAL = "#8a8984"     # reference lines and their labels

TYPE_LABELS = {"cafe": "Cafe", "restaurant": "Restaurant", "quick_service": "Quick service",
               "bakery": "Bakery", "grocery": "Grocery"}
LABEL_TO_TYPE = {label: key for key, label in TYPE_LABELS.items()}
BUILDING_TYPES = {"shopping_centre": "Shopping centre", "food_court": "Food court",
                  "university": "University campus", "commercial_building": "Commercial building",
                  "hospitality": "Hospitality venue"}
LETTERS = {"offsite": "A", "hybrid": "B", "onsite": "C"}
PATH_ORDER = ["On-site", "Hybrid", "Off-site FOGO"]   # top to bottom on the tipping chart

DEFAULTS = {"building_name": "My building", "building_type": "food_court", "tenant_count": 6,
            "total_kg": 0.0, "current_collections": 0, "room_m2": 10.0, "space_m2": 0.0,
            "cost_week": 0.0, "local_use": "No", "budget": "low", "growth": 0.0,
            "step": "input", "editor_version": 0}


def tenants_frame(rows=None):
    rows = rows or [{"type": "cafe", "size": "medium", "count": 1}]
    return pd.DataFrame([{"Type": TYPE_LABELS[r["type"]], "Size": r.get("size", "medium").title(),
                          "Count": int(r.get("count", 1)),
                          "Measured kg/week": float(r["kg_week"]) if r.get("kg_week") is not None else float("nan")}
                         for r in rows])


def bins_frame(rows=None):
    rows = rows or [{"size_l": 240, "count": 2, "collections_per_week": 2}]
    return pd.DataFrame([{"Bin size (L)": int(r["size_l"]), "Count": int(r["count"]),
                          "Collections/week": int(r["collections_per_week"])} for r in rows])


def init_state():
    for key, value in DEFAULTS.items():
        st.session_state.setdefault(key, value)
    st.session_state.setdefault("tenants_df", tenants_frame())
    st.session_state.setdefault("bins_df", bins_frame())


def load_example(key):
    ex = EXAMPLES[key]
    st.session_state.update({
        "building_name": ex["building_name"], "building_type": ex["building_type"],
        "tenant_count": sum(int(t.get("count", 1)) for t in ex.get("tenants", [])),
        "total_kg": float(ex.get("total_food_waste_kg_week") or 0.0),
        "current_collections": int(ex["current_collections_per_week"]),
        "room_m2": float(ex["waste_room_area_m2"]), "space_m2": float(ex["onsite_space_m2"]),
        "cost_week": float(ex.get("current_collection_cost_aud_week") or 0.0),
        "local_use": "Yes" if ex["local_use"] else "No", "budget": ex["budget_level"],
        "growth": float(ex.get("annual_change_pct") or 0.0),
        "tenants_df": tenants_frame(ex.get("tenants")), "bins_df": bins_frame(ex["general_waste_bins"]),
        "editor_version": st.session_state.editor_version + 1, "step": "input",
    })


def collect_inputs(tenants_df, bins_df):
    tenants = []
    for _, r in tenants_df.iterrows():
        if pd.isna(r.get("Type")) or r.get("Type") not in LABEL_TO_TYPE:
            continue
        t = {"name": r["Type"], "type": LABEL_TO_TYPE[r["Type"]],
             "size": str(r.get("Size") if not pd.isna(r.get("Size")) else "Medium").lower(),
             "count": int(r.get("Count")) if not pd.isna(r.get("Count")) else 1}
        if not pd.isna(r.get("Measured kg/week")):
            t["kg_week"] = float(r["Measured kg/week"])
        tenants.append(t)
    bins = []
    for _, r in bins_df.iterrows():
        if any(pd.isna(r.get(c)) for c in ["Bin size (L)", "Count", "Collections/week"]):
            continue
        if int(r["Count"]) > 0 and int(r["Collections/week"]) > 0:
            bins.append({"size_l": int(r["Bin size (L)"]), "count": int(r["Count"]),
                         "collections_per_week": int(r["Collections/week"])})
    total = float(st.session_state.total_kg or 0)
    return {
        "building_name": st.session_state.building_name, "building_type": st.session_state.building_type,
        "number_of_food_tenants": int(st.session_state.tenant_count),
        "total_food_waste_kg_week": total if total > 0 else None, "tenants": tenants,
        "current_collections_per_week": int(st.session_state.current_collections),
        "general_waste_bins": bins, "waste_room_area_m2": float(st.session_state.room_m2),
        "onsite_space_m2": float(st.session_state.space_m2),
        "local_use": st.session_state.local_use == "Yes", "budget_level": st.session_state.budget,
        "current_collection_cost_aud_week": float(st.session_state.cost_week) or None,
        "annual_change_pct": float(st.session_state.growth),
    }


# ---------------------------------------------------------------- formatting
def rng(d, unit, digits=0):
    f = f"{{:,.{digits}f}}"
    return f"{f.format(d['base'])} {unit} ({f.format(d['low'])} to {f.format(d['high'])})"


def steps_header():
    names = [("input", "1 Input"), ("compare", "2 Compare"), ("plan", "3 Plan")]
    parts = [f"**{label}**" if st.session_state.step == key else label for key, label in names]
    st.markdown("  ›  ".join(parts))


# ---------------------------------------------------------------- 1 input
def input_page():
    left, right = st.columns([1, 2], gap="large")
    with left:
        st.header("What should your building do with its food waste?")
        st.write("Tell us about your building and we'll compare three options: external FOGO collection, "
                 "hybrid, and on-site processing.")
        st.caption("New here? Try an example first")
        if st.button("Case 1: Small cafe building", width="stretch"):
            load_example("case_1_small_cafe_building")
            st.rerun()
        if st.button("Case 2: Shopping centre food court", width="stretch"):
            load_example("case_2_shopping_centre_food_court")
            st.rerun()
        st.caption("Examples use illustrative data.")

    ver = st.session_state.editor_version
    with right:
        st.subheader("Building")
        c1, c2, c3 = st.columns(3)
        c1.text_input("Building name", key="building_name")
        c2.selectbox("Building type", list(BUILDING_TYPES), format_func=BUILDING_TYPES.get, key="building_type")
        c3.number_input("Number of food tenants", min_value=0, step=1, key="tenant_count")

        st.subheader("Food waste")
        c1, c2 = st.columns(2)
        c1.number_input("Total food waste (kg/week)", min_value=0.0, step=10.0, key="total_kg",
                        help="Leave at 0 to estimate it from the tenants below.")
        c2.number_input("Current organics collections per week", min_value=0, max_value=14, step=1,
                        key="current_collections")
        with st.expander("Not sure? Enter by tenant", expanded=st.session_state.total_kg == 0):
            tenants = st.data_editor(
                st.session_state.tenants_df, key=f"tenants_{ver}", num_rows="dynamic", width="stretch",
                column_config={
                    "Type": st.column_config.SelectboxColumn(options=list(TYPE_LABELS.values()), required=True),
                    "Size": st.column_config.SelectboxColumn(options=["Small", "Medium", "Large"], required=True),
                    "Count": st.column_config.NumberColumn(min_value=1, step=1, required=True),
                    "Measured kg/week": st.column_config.NumberColumn(
                        min_value=0, help="Optional. A weighed figure replaces the estimate for this row."),
                })
            st.caption("Estimates use illustrative medium-tenant values from the assumptions sheet; "
                       "a weighed audit is better.")

        st.subheader("General waste bins")
        st.caption("Your general (landfill) waste bins only, not recycling. Used for the NSW mandate check.")
        bins = st.data_editor(
            st.session_state.bins_df, key=f"bins_{ver}", num_rows="dynamic", width="stretch",
            column_config={
                "Bin size (L)": st.column_config.SelectboxColumn(options=[120, 240, 360, 660, 1100], required=True),
                "Count": st.column_config.NumberColumn(min_value=0, step=1, required=True),
                "Collections/week": st.column_config.NumberColumn(min_value=0, max_value=14, step=1, required=True),
            })

        st.subheader("Space and cost")
        c1, c2 = st.columns(2)
        c1.number_input("Waste room area (m²)", min_value=0.0, step=1.0, key="room_m2")
        c2.number_input("Space for on-site processing (m²)", min_value=0.0, step=1.0, key="space_m2",
                        help=f"0 if none. Under {v(CFG, 'space_moderate_min_m2'):g} m² is too little for "
                             "on-site processing.")
        c1.number_input("Current collection cost (AUD/week, optional)", min_value=0.0, step=10.0, key="cost_week")
        c2.radio("Local use for processed material?", ["Yes", "No"], horizontal=True, key="local_use",
                 help="For example landscaping, a rooftop garden or a processor contract.")
        c1.selectbox("Budget for on-site equipment", ["low", "medium", "high"],
                     format_func=lambda k: f"{k.title()}: {BUDGET[k]}", key="budget")
        c2.slider("Expected change in food waste per year (%)", -5.0, 10.0, step=0.5, key="growth")

        if st.button("Compare the three options →", type="primary"):
            inputs = collect_inputs(tenants, bins)
            W = waste_profile(inputs, CFG)["total_kg_week"]
            if W <= 0:
                st.error("Enter the total food waste, or at least one tenant.")
            else:
                st.session_state.update({"tenants_df": tenants, "bins_df": bins, "inputs": inputs,
                                         "result": plan_building(inputs, CFG), "step": "compare",
                                         "editor_version": ver + 1})
                st.rerun()


# ---------------------------------------------------------------- 2 compare
def mandate_banner(m):
    if m["status_code"] == "unknown":
        st.info(m["status_text"])
        return
    line = f"**{m['status_text']}** · general waste capacity {m['capacity_l_week']:,.0f} L/week"
    if m["status_code"] != "below":
        line += f" (threshold {m['threshold_l_week']:,.0f} L/week)"
    (st.warning if m["status_code"] == "covered_2026" else st.info)(line)
    with st.expander("What this means for your building"):
        for note in m["notes"]:
            st.markdown(f"- {note}")


def comparison_table(result):
    rec, comp = result["recommendation"], result["comparison"]
    cols = {p: f"{LETTERS[p]} · {LABELS[p]}" + ("  (recommended)" if p == rec["pathway"] else "")
            for p in PATHWAYS}
    rows = {
        "Sent off-site (kg/week)": lambda c: f"{c['offsite_kg_week']:,.0f}",
        "Processed on-site (kg/week)": lambda c: f"{c['onsite_kg_week']:,.0f}",
        "Bins needed (240 L)": lambda c: f"{c['bins']}" + ("" if c["room_ok"] else " (waste room too small)"),
        "Collections per week": lambda c: (f"{c['collections_per_week']} ("
                                           + " · ".join(c["collection_days"]) + ")"),
        "Bin lifts per week": lambda c: f"{c['lifts_per_week']}",
        "Indicative collection cost (AUD/week, ex GST)": lambda c: f"${c['collection_cost_aud_week']:,.0f}",
        "Space needed": lambda c: c["space"],
        "Upfront cost": lambda c: c["cost"],
        "Operational effort": lambda c: c["effort"],
        "Diverted from landfill (kg/week)": lambda c: f"{c['diverted_kg_week']:,.0f}",
        "Landfill methane avoided (kg CH₄/year)": lambda c: rng(c["ch4_avoided_kg_year"], "kg"),
        "Net GHG saving (t CO₂e/year)": lambda c: rng(c["net_ghg_t_year"], "t", 1),
        "Equipment budget (indicative)": lambda c: ("None" if not c["equipment_budget"] else
                                                    f"${c['equipment_budget']['min'] / 1000:,.0f}k to "
                                                    f"${c['equipment_budget']['max'] / 1000:,.0f}k"),
    }
    table = pd.DataFrame({cols[p]: [fn(comp[p]) for fn in rows.values()] for p in PATHWAYS},
                         index=list(rows.keys()))
    table.index.name = "Criteria"
    st.dataframe(table, width="stretch", height=(len(table) + 1) * 35 + 3)
    st.caption("Every number comes from the assumptions sheet (see Data & sources). Ranges are low and high "
               "planning scenarios, not statistical intervals. Methane avoided is the same for every pathway "
               "because the same food leaves landfill; net GHG differs by how it is processed.")


def tipping_chart(inputs, W):
    top = max(3000.0, W * 1.5)
    step = max(10.0, round(top / 150, -1))
    space, use, budget = float(inputs["onsite_space_m2"]), bool(inputs["local_use"]), inputs["budget_level"]
    rows = []
    x = 0.0
    while x <= top:
        rows.append({"Weekly food waste (kg)": x, "Pathway": recommend(x, space, use, budget, CFG)["label"]})
        x += step
    df = pd.DataFrame(rows)
    line = alt.Chart(df).mark_line(interpolate="step-after", strokeWidth=2, color=SERIES).encode(
        x=alt.X("Weekly food waste (kg):Q", title="Weekly food waste (kg)"),
        y=alt.Y("Pathway:N", sort=PATH_ORDER, scale=alt.Scale(domain=PATH_ORDER), title=None),
        order=alt.Order("Weekly food waste (kg):Q"),
        tooltip=[alt.Tooltip("Weekly food waste (kg):Q", format=",.0f"), "Pathway:N"])
    you = pd.DataFrame({"Weekly food waste (kg)": [W], "label": [f"This building: {W:,.0f} kg"]})
    rule = alt.Chart(you).mark_rule(strokeDash=[4, 4], color=NEUTRAL).encode(x="Weekly food waste (kg):Q")
    text = alt.Chart(you).mark_text(align="left", dx=6, dy=-6, color=NEUTRAL).encode(
        x="Weekly food waste (kg):Q", y=alt.value(0), text="label:N")
    st.altair_chart((line + rule + text).properties(height=200), width="stretch")
    st.caption("Holding this building's space, local use and budget constant. The answer only moves up when "
               "the other conditions are met too.")


def compare_page(result):
    rec = result["recommendation"]
    mandate_banner(result["mandate"])
    st.subheader("Recommended for this building")
    st.success(f"**Recommended path: {rec['label']}**")
    st.markdown("**Why?**\n" + "\n".join(f"- {r}" for r in rec["reasons"]))
    st.markdown(f"**What would change this:** {rec['what_would_change']}")
    if rec["r5_note"]:
        st.info(rec["r5_note"])
    for w in rec["warnings"]:
        st.warning(w)
    st.subheader("Compare the three options")
    comparison_table(result)
    st.subheader("At what weekly volume does the best option change?")
    tipping_chart(st.session_state.inputs, result["waste_profile"]["total_kg_week"])
    c1, c2 = st.columns([1, 1])
    if c1.button("← Edit inputs"):
        st.session_state.step = "input"
        st.rerun()
    if c2.button("View implementation plan →", type="primary"):
        st.session_state.step = "plan"
        st.rerun()


# ---------------------------------------------------------------- 3 plan
def roadmap_chart(result, inputs):
    W = result["waste_profile"]["total_kg_week"]
    g = float(inputs.get("annual_change_pct") or 0) / 100
    df = pd.DataFrame({"Year": list(range(2026, 2036))})
    df["Food waste (kg/week)"] = [round(W * (1 + g) ** (y - 2026), 0) for y in df["Year"]]
    refs = pd.DataFrame({"kg": [v(CFG, "t1_hybrid_kg_week"), v(CFG, "t2_onsite_kg_week")],
                         "label": [f"Hybrid threshold {v(CFG, 't1_hybrid_kg_week'):,.0f} kg",
                                   f"On-site threshold {v(CFG, 't2_onsite_kg_week'):,.0f} kg"]})
    base = alt.Chart(df).encode(x=alt.X("Year:O", title=None, axis=alt.Axis(labelAngle=0)))
    line = base.mark_line(strokeWidth=2, color=SERIES).encode(
        y=alt.Y("Food waste (kg/week):Q", title="Food waste (kg/week)",
                scale=alt.Scale(domain=[0, max(df["Food waste (kg/week)"].max(), refs["kg"].max()) * 1.1])))
    points = base.mark_point(size=60, filled=True, color=SERIES).encode(
        y="Food waste (kg/week):Q", tooltip=["Year:O", alt.Tooltip("Food waste (kg/week):Q", format=",.0f")])
    rules = alt.Chart(refs).mark_rule(strokeDash=[4, 4], color=NEUTRAL).encode(y="kg:Q")
    labels = alt.Chart(refs).mark_text(align="left", dx=4, dy=-6, color=NEUTRAL).encode(
        y="kg:Q", x=alt.value(0), text="label:N")
    st.altair_chart((line + points + rules + labels).properties(height=260), width="stretch")


def plan_page(result):
    p, rec, rm = result["plan"], result["recommendation"], result["roadmap"]
    st.header(f"Implementation plan · {result['building_name'] or 'Your building'}")
    st.subheader(f"{rec['label']} rollout plan")
    st.write(rec["reasons"][0])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Bins", f"{p['bins']} × {p['bin_size_l']} L")
    c2.metric("Collections", f"{p['collections_per_week']} per week")
    c2.caption(" · ".join(p["collection_days"]) or "No off-site collection")
    c3.metric("Sent off-site", f"{p['offsite_kg_week']:,.0f} kg/week")
    c4.metric("Processed on-site", f"{p['onsite_kg_week']:,.0f} kg/week")

    st.subheader("Expected impact")
    c1, c2, c3 = st.columns(3)
    c1.metric("Diverted from landfill", f"{p['diverted_kg_year']:,.0f} kg/year")
    c2.metric("Landfill methane avoided", f"{p['ch4_avoided_kg_year']['base']:,.0f} kg CH₄/year")
    c2.caption(f"Range {p['ch4_avoided_kg_year']['low']:,.0f} to {p['ch4_avoided_kg_year']['high']:,.0f}")
    c3.metric("Net GHG saving", f"{p['net_ghg_t_year']['base']:,.1f} t CO₂e/year")
    c3.caption(f"Range {p['net_ghg_t_year']['low']:,.1f} to {p['net_ghg_t_year']['high']:,.1f}")
    st.caption("Emission factors: NSW EPA organics processing technology assessment (2023). "
               "Bin density: NSW EPA C&I waste audit (2024). See Data & sources.")

    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("Next steps")
        st.markdown("\n".join(f"{i}. {s}" for i, s in enumerate(p["next_steps"], 1)))
        if p["local_use_line"]:
            st.info(p["local_use_line"])
    with right:
        st.subheader("Collection change")
        change = p["collections_change"]
        st.write(f"{p['collections_per_week']} collections per week "
                 f"({'+' if change >= 0 else ''}{change} compared with now), {p['lifts_per_week']} bin lifts, "
                 f"about ${p['collection_cost_aud_week']:,.0f} per week at Sydney rates (ex GST, indicative).")
        cost_now = st.session_state.inputs.get("current_collection_cost_aud_week")
        if cost_now:
            st.caption(f"Current collection cost entered: ${cost_now:,.0f} per week.")

    st.subheader("Roadmap to 2035")
    roadmap_chart(result, st.session_state.inputs)
    table = pd.DataFrame([{"Year": str(r["year"]), "Food waste (kg/week)": f"{r['food_waste_kg_week']:,.0f}",
                           "NSW mandate": r["mandate"], "Recommended pathway": r["pathway"],
                           "What moves it up": r["next_step"], "Action": r["action"]} for r in rm["rows"]])
    st.table(table.set_index("Year"))
    cum = rm["cumulative_net_ghg_t_2026_2035"]
    st.caption(f"Net GHG saving 2026 to 2035 (indicative): {cum['base']:,.0f} t CO₂e "
               f"(range {cum['low']:,.0f} to {cum['high']:,.0f}). {rm['note']}")

    if st.button("← Back to comparison"):
        st.session_state.step = "compare"
        st.rerun()
    st.caption("To save this plan as a PDF, use your browser's Print and choose Save as PDF.")


# ---------------------------------------------------------------- other pages
def data_page():
    st.header("Data & sources")
    st.write("Every number the planner uses, with its range, confidence and source. "
             "H = directly supported, M = modelled or vendor evidence needing site checks, "
             "L = proposed team assumption.")
    df = pd.read_csv(HERE / "assumptions.csv")
    df["source_url"] = df["source_url"].fillna("").str.split(";").str[0]
    st.dataframe(df[["item", "unit", "min", "base", "max", "confidence", "source_id", "source_url", "notes", "key"]],
                 hide_index=True, width="stretch",
                 column_config={"source_url": st.column_config.LinkColumn("Source link"),
                                "item": "Item", "unit": "Unit", "min": "Min", "base": "Base", "max": "Max",
                                "confidence": "Conf.", "source_id": "Source", "notes": "Notes", "key": "Key"})


def how_page():
    st.header("How it works")
    st.markdown(f"""
1. **Mandate check.** Weekly general waste capacity = bin size × number of bins × collections per week.
   It is compared with the NSW EPA phases (1 July 2026, 2028 and 2030). Exemptions are not modelled.
2. **Three pathways.** Off-site FOGO collection, Hybrid (part processed on site) and On-site (larger system).
3. **Recommendation rules.**

| Rule | Condition | Result |
|---|---|---|
| R0 | Default | Off-site FOGO |
| R1 | On-site space under {v(CFG, 'space_moderate_min_m2'):g} m² | Hybrid and On-site excluded |
| R2 | Food waste ≥ {v(CFG, 't1_hybrid_kg_week'):,.0f} kg/week, space ≥ {v(CFG, 'space_moderate_min_m2'):g} m², a local use and a Medium or High budget | Hybrid |
| R3 | Food waste ≥ {v(CFG, 't2_onsite_kg_week'):,.0f} kg/week, space ≥ {v(CFG, 'space_ample_min_m2'):g} m² and a High budget | On-site, with a safety check |
| R4 | On-site qualifies but there is no local use | Off-site FOGO |
| R5 | Off-site needs {v(CFG, 'r5_high_collections_per_week'):g}+ collections a week and Hybrid would need fewer | A note only |

4. **Plan and impact.** Bins are sized to the longest gap between collections; impact shows landfill methane
   avoided and net GHG saving as ranges.
5. **Roadmap to 2035.** Volume grows by your yearly change; the same rules run again each year.
""")


def about_page():
    st.header("About")
    st.write("Built for Climate Hack-tion 2026, challenge “Build for 2035”, COP31 priority: "
             "Zero Waste & Methane Reduction.")
    st.markdown("""
- **Team:** Yuna Kim (lead, rules, testing), Jongyoon Yoo (screen design, demo, README),
  Youngjun Cho (engine and app), Yeonsu Kim (research and data)
- **Tools:** Python, Streamlit, pandas, Altair, pytest; AI assistance from Claude (Anthropic) for drafting
  documents and code
- **Guidance only.** Not legal advice. Confirm mandate duties with NSW EPA or your council, and get quotes
  and approvals before buying equipment.
""")


# ---------------------------------------------------------------- main
init_state()
# Keep form values when the input widgets are not on screen (Compare/Plan pages):
# re-assigning a widget key at the top of the run stops Streamlit from clearing it.
for _key in ["building_name", "building_type", "tenant_count", "total_kg", "current_collections", "room_m2",
             "space_m2", "cost_week", "local_use", "budget", "growth"]:
    st.session_state[_key] = st.session_state[_key]
page = st.sidebar.radio("Menu", ["Planner", "How it works", "Data & sources", "About"])
st.sidebar.caption("Circular Organics Planner · illustrative prototype")

if page == "Planner":
    st.title("Circular Organics Planner")
    steps_header()
    if st.session_state.step != "input" and "result" not in st.session_state:
        st.session_state.step = "input"
    if st.session_state.step == "input":
        input_page()
    elif st.session_state.step == "compare":
        compare_page(st.session_state.result)
    else:
        plan_page(st.session_state.result)
elif page == "How it works":
    how_page()
elif page == "Data & sources":
    data_page()
else:
    about_page()
