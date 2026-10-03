"""Streamlit interface for the Circular Organics Planner.

All planning decisions and calculated values come from app.engine.
"""
import json
import inspect
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT))

from app.engine import (  # noqa: E402
    LABELS, PATHWAYS, budget_bands, load_config, plan_building, v, waste_profile,
)

st.set_page_config(page_title="Circular Organics Planner", layout="wide")
st.markdown("""
<style>
    .stMainBlockContainer {max-width: 1040px; padding-top: 2.5rem; padding-bottom: 4rem;}
    h1, h2, h3 {letter-spacing: -0.025em; color: #1f3829;}
    h1 {font-size: clamp(2.35rem, 5vw, 4rem); line-height: 1.02;}
    h2 {margin-top: 1.5rem;}
    [data-testid="stSidebar"] {background: #e9ede5; border-right: 1px solid #d7ddd4;}
    [data-testid="stMetric"] {background: #ffffff; border: 1px solid #dce2da; border-radius: 14px; padding: 1rem 1.1rem;}
    [data-testid="stMetricLabel"] {color: #587063;}
    [data-testid="stMetricValue"] {color: #1f3829;}
    .stButton > button[kind="primary"] {border-radius: 999px; padding: .65rem 1.5rem; font-weight: 650;}
    .stButton > button[kind="secondary"] {border-radius: 999px;}
    [data-testid="stAlert"] {border-radius: 12px;}
    hr {border-color: #dce2da; margin: 2rem 0;}
    .eyebrow {color:#557a62; font-size:.78rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase;}
    .lead {font-size:1.2rem; line-height:1.55; max-width:700px; color:#4f6156;}
    .step {color:#66766c; font-size:.9rem; font-weight:600; margin-bottom:.5rem;}
    .pathway {font-size:clamp(3rem, 8vw, 5.5rem); line-height:1; color:#294f37; font-weight:750; letter-spacing:-.055em; margin:.2rem 0 .75rem;}
    .result-note {font-size:1.1rem; line-height:1.5; color:#46594d; max-width:760px;}
</style>
""", unsafe_allow_html=True)
CFG = load_config(DATA / "assumptions.csv")
EXAMPLES = json.loads((DATA / "examples.json").read_text(encoding="utf-8"))
BUDGET_LABELS = budget_bands(CFG)

TENANT_TYPES = {
    "cafe": "Cafe", "restaurant": "Restaurant", "quick_service": "Quick service",
    "bakery": "Bakery", "grocery": "Grocery",
}
TYPE_KEYS = {label: key for key, label in TENANT_TYPES.items()}
BUILDING_TYPES = {
    "shopping_centre": "Shopping centre", "food_court": "Food court",
    "university": "University campus", "commercial_building": "Commercial building",
    "hospitality": "Hospitality venue",
}
INPUT_KEYS = (
    "building_name", "building_type", "tenant_count", "total_kg", "current_collections",
    "room_m2", "space_m2", "cost_week", "local_use", "budget", "growth",
)


def tenant_frame(rows=None):
    rows = rows or [{"name": "Cafe", "type": "cafe", "size": "medium", "count": 1}]
    return pd.DataFrame([
        {
            "Tenant": row.get("name", TENANT_TYPES[row["type"]]),
            "Type": TENANT_TYPES[row["type"]],
            "Size": row.get("size", "medium").title(),
            "Count": int(row.get("count", 1)),
            "Measured kg/week": row.get("kg_week"),
        }
        for row in rows
    ])


def bin_frame(rows=None):
    rows = rows or [{"size_l": 240, "count": 2, "collections_per_week": 2}]
    return pd.DataFrame([
        {"Bin size (L)": int(row["size_l"]), "Count": int(row["count"]),
         "Collections/week": int(row["collections_per_week"])}
        for row in rows
    ])


def initialise_state():
    defaults = {
        "building_name": "My building", "building_type": "food_court", "tenant_count": 6,
        "total_kg": 0.0, "current_collections": 0, "room_m2": 10.0,
        "space_m2": 0.0, "cost_week": 0.0, "local_use": "No", "budget": "low",
        "growth": 0.0, "tenants_df": tenant_frame(), "bins_df": bin_frame(),
        "show_results": False, "input_step": "waste", "editor_version": 0,
        "multiple_bin_types": False, "bin_size": 240, "bin_count": 2,
        "bin_collections": 2,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)
    # Preserve widget values while the inputs are hidden on the results/About page.
    for key in INPUT_KEYS:
        st.session_state[key] = st.session_state[key]


def load_example(key):
    example = EXAMPLES[key]
    st.session_state.update({
        "building_name": example["building_name"],
        "building_type": example["building_type"],
        "tenant_count": sum(int(t.get("count", 1)) for t in example.get("tenants", [])),
        "total_kg": float(example.get("total_food_waste_kg_week") or 0),
        "current_collections": int(example["current_collections_per_week"]),
        "room_m2": float(example["waste_room_area_m2"]),
        "space_m2": float(example["onsite_space_m2"]),
        "cost_week": float(example.get("current_collection_cost_aud_week") or 0),
        "local_use": "Yes" if example["local_use"] else "No",
        "budget": example["budget_level"],
        "growth": float(example.get("annual_change_pct") or 0),
        "tenants_df": tenant_frame(example.get("tenants")),
        "bins_df": bin_frame(example["general_waste_bins"]),
        "bin_size": int(example["general_waste_bins"][0]["size_l"]),
        "bin_count": int(example["general_waste_bins"][0]["count"]),
        "bin_collections": int(example["general_waste_bins"][0]["collections_per_week"]),
        "multiple_bin_types": len(example["general_waste_bins"]) > 1,
        "editor_version": st.session_state.editor_version + 1,
        "show_results": False, "input_step": "waste",
    })


def collect_inputs(tenants_df, bins_df):
    tenants = []
    for _, row in tenants_df.iterrows():
        if row.get("Type") not in TYPE_KEYS:
            continue
        tenant = {
            "name": str(row.get("Tenant") or row["Type"]),
            "type": TYPE_KEYS[row["Type"]],
            "size": str(row.get("Size") if not pd.isna(row.get("Size")) else "Medium").lower(),
            "count": int(row["Count"]) if not pd.isna(row.get("Count")) else 1,
        }
        if not pd.isna(row.get("Measured kg/week")):
            tenant["kg_week"] = float(row["Measured kg/week"])
        tenants.append(tenant)

    bins = []
    for _, row in bins_df.iterrows():
        if any(pd.isna(row.get(col)) for col in ("Bin size (L)", "Count", "Collections/week")):
            continue
        if int(row["Count"]) > 0 and int(row["Collections/week"]) > 0:
            bins.append({
                "size_l": int(row["Bin size (L)"]), "count": int(row["Count"]),
                "collections_per_week": int(row["Collections/week"]),
            })

    state = st.session_state
    return {
        "building_name": state.building_name,
        "building_type": state.building_type,
        "number_of_food_tenants": int(state.tenant_count),
        "total_food_waste_kg_week": float(state.total_kg) or None,
        "tenants": tenants,
        "current_collections_per_week": int(state.current_collections),
        "general_waste_bins": bins,
        "waste_room_area_m2": float(state.room_m2),
        "onsite_space_m2": float(state.space_m2),
        "local_use": state.local_use == "Yes",
        "budget_level": state.budget,
        "current_collection_cost_aud_week": float(state.cost_week) or None,
        "annual_change_pct": float(state.growth),
    }


def example_picker():
    with st.expander("Try an example"):
        choice = st.selectbox(
            "Example building",
            ["case_1_small_cafe_building", "case_2_shopping_centre_food_court"],
            format_func=lambda key: ("Small cafe building" if key.startswith("case_1")
                                     else "Shopping centre food court"),
            label_visibility="collapsed",
        )
        st.button("Load example", on_click=load_example, args=(choice,))
        st.caption("Examples use illustrative data.")


def waste_step():
    st.markdown('<div class="step">Step 1 of 2 · Waste</div>', unsafe_allow_html=True)
    st.header("How much food waste does your building generate?")
    st.write("Use a measured weekly figure if you have one.")
    st.number_input(
        "Food waste", min_value=0.0, step=10.0, key="total_kg",
        help="Leave at zero to estimate from tenants.",
        label_visibility="collapsed",
    )
    st.caption("kg per week")
    version = st.session_state.editor_version
    with st.expander("Estimate from tenants"):
        tenants = st.data_editor(
            st.session_state.tenants_df, key=f"tenants_{version}", num_rows="dynamic",
            width="stretch",
            column_config={
                "Tenant": st.column_config.TextColumn(required=True),
                "Type": st.column_config.SelectboxColumn(options=list(TENANT_TYPES.values()), required=True),
                "Size": st.column_config.SelectboxColumn(
                    options=["Small", "Medium", "Large"], required=True),
                "Count": st.column_config.NumberColumn(min_value=1, step=1, required=True),
                "Measured kg/week": st.column_config.NumberColumn(
                    min_value=0, help="Optional weighed amount per tenant; replaces the type estimate."),
            },
        )
        st.caption("Tenant estimates are illustrative. A seven-day weighed audit gives a better input.")
    st.session_state.tenants_draft = tenants
    if st.button("Continue to site details", type="primary"):
        provisional = collect_inputs(tenants, bin_frame())
        if waste_profile(provisional, CFG)["total_kg_week"] <= 0:
            st.error("Enter weekly food waste or add at least one tenant estimate.")
        else:
            st.session_state.tenants_df = tenants
            st.session_state.input_step = "site"
            st.rerun()
    example_picker()


def site_step():
    st.markdown('<div class="step">Step 2 of 2 · Site</div>', unsafe_allow_html=True)
    st.header("What will work at your site?")
    st.write("These details determine NSW mandate timing and which pathway fits.")
    st.subheader("General waste service")
    st.caption("Landfill bins only — exclude recycling and existing organics bins.")
    a, b, c = st.columns(3)
    a.selectbox("Bin size", [120, 240, 360, 660, 1100], key="bin_size",
                format_func=lambda value: f"{value} L")
    b.number_input("Number of bins", min_value=1, step=1, key="bin_count")
    c.number_input("Collections per week", min_value=1, max_value=14, step=1,
                   key="bin_collections")

    st.checkbox("Add another bin type", key="multiple_bin_types")
    if st.session_state.multiple_bin_types:
        st.caption("Add each general-waste bin type used at the building.")
        bins = st.data_editor(
            st.session_state.bins_df, key=f"bins_{st.session_state.editor_version}",
            num_rows="dynamic", width="stretch",
            column_config={
                "Bin size (L)": st.column_config.SelectboxColumn(
                    options=[120, 240, 360, 660, 1100], required=True),
                "Count": st.column_config.NumberColumn(min_value=0, step=1, required=True),
                "Collections/week": st.column_config.NumberColumn(
                    min_value=0, max_value=14, step=1, required=True),
            },
        )
    else:
        bins = bin_frame([{"size_l": st.session_state.bin_size,
                           "count": st.session_state.bin_count,
                           "collections_per_week": st.session_state.bin_collections}])

    st.subheader("On-site conditions")
    a, b, c = st.columns(3)
    a.number_input("Processing space (m²)", min_value=0.0, step=1.0, key="space_m2")
    b.radio("Local use for output?", ["Yes", "No"], horizontal=True, key="local_use",
            help="For example, landscaping or a processor contract.")
    c.selectbox("Equipment budget", ["low", "medium", "high"],
                format_func=lambda key: f"{key.title()} · {BUDGET_LABELS[key]}", key="budget")

    with st.expander("Advanced details"):
        a, b, c = st.columns(3)
        a.text_input("Building name", key="building_name")
        b.selectbox("Building type", list(BUILDING_TYPES), format_func=BUILDING_TYPES.get,
                    key="building_type")
        c.number_input("Number of food tenants", min_value=0, step=1, key="tenant_count")
        a.number_input("Current organics collections/week", min_value=0, max_value=14,
                       step=1, key="current_collections")
        b.number_input("Current collection cost (AUD/week)", min_value=0.0,
                       step=10.0, key="cost_week")
        c.number_input("Waste room area (m²)", min_value=0.0, step=1.0, key="room_m2")
        a.slider("Expected annual food-waste change (%)", -5.0, 10.0, step=0.5,
                 key="growth")
    back, submit = st.columns([1, 2])
    if back.button("← Back"):
        st.session_state.input_step = "waste"
        st.rerun()
    if submit.button("Compare my options", type="primary", width="stretch"):
        inputs = collect_inputs(st.session_state.tenants_df, bins)
        st.session_state.update({
            "inputs": inputs, "result": plan_building(inputs, CFG),
            "bins_df": bins, "show_results": True,
            "editor_version": st.session_state.editor_version + 1,
            "scroll_to_result": True,
        })
        st.rerun()


def input_page():
    st.markdown('<div class="eyebrow">Circular Organics Planner</div>', unsafe_allow_html=True)
    st.title("Find the right food-waste setup for your building.")
    st.markdown(
        '<div class="lead">Turn your waste volume and site conditions into a clear pathway, '
        'a practical collection plan, and an estimate of landfill methane avoided.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    if st.session_state.input_step == "waste":
        waste_step()
    else:
        site_step()


def mandate_banner(mandate):
    if mandate["status_code"] == "unknown":
        st.info(mandate["status_text"])
        return
    message = f"**NSW FOGO status · {mandate['status_text']}**"
    (st.warning if mandate["status_code"] == "covered_2026" else st.info)(message)


def mandate_details(mandate):
    with st.expander("NSW mandate details and exemptions"):
        if mandate["capacity_l_week"] is not None:
            st.write(f"General-waste capacity: **{mandate['capacity_l_week']:,.0f} L/week**")
            if mandate["status_code"] != "below":
                st.write(f"Relevant threshold: **{mandate['threshold_l_week']:,.0f} L/week**")
        st.markdown("\n".join(f"- {note}" for note in mandate["notes"]))


def simple_comparison(result):
    rows = []
    for pathway in PATHWAYS:
        item = result["comparison"][pathway]
        rows.append({
            "Pathway": LABELS[pathway] +
            (" · Recommended" if pathway == result["recommendation"]["pathway"] else ""),
            "Waste split": (f"{item['onsite_kg_week']:,.0f} on-site / "
                            f"{item['offsite_kg_week']:,.0f} off-site kg/week"),
            "Bins": f"{item['bins']} × {item['bin_size_l']} L",
            "Collections": f"{item['collections_per_week']}/week",
            "Space": item["space"],
            "Effort": item["effort"],
            "Collection cost": f"${item['collection_cost_aud_week']:,.0f}/week",
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


def full_comparison(result, local_use):
    comparison = result["comparison"]
    rows = {
        "Sent off-site (kg/week)": lambda x: f"{x['offsite_kg_week']:,.0f}",
        "Processed on-site (kg/week)": lambda x: f"{x['onsite_kg_week']:,.0f}",
        "Output use": lambda x: ("Composted off site" if x["onsite_kg_week"] == 0 else
                                 "Pre-processed on site for local use; remainder composted off site"
                                 if local_use else
                                 "Pre-processed on site; no local use confirmed; remainder composted off site"),
        "Bins needed": lambda x: f"{x['bins']} × {x['bin_size_l']} L" +
        (" (waste room too small)" if not x["room_ok"] else ""),
        "Collections per week": lambda x: f"{x['collections_per_week']} ({' · '.join(x['collection_days'])})",
        "Bin lifts per week": lambda x: str(x["lifts_per_week"]),
        "Bin footprint (m²)": lambda x: f"{x['bins_floor_m2']:,.2f}",
        "Indicative collection cost (AUD/week, ex GST)": lambda x: f"${x['collection_cost_aud_week']:,.0f}",
        "Space needed": lambda x: x["space"],
        "Upfront cost": lambda x: x["cost"],
        "Operational effort": lambda x: x["effort"],
        "Diverted from landfill (kg/week)": lambda x: f"{x['diverted_kg_week']:,.0f}",
        "Landfill methane avoided (kg CH₄/year)": lambda x: range_text(x["ch4_avoided_kg_year"]),
        "Net GHG saving (t CO₂e/year)": lambda x: range_text(x["net_ghg_t_year"], 1),
        "Equipment budget (indicative)": lambda x: "None" if not x["equipment_budget"] else
        f"${x['equipment_budget']['min']:,.0f}–${x['equipment_budget']['max']:,.0f}",
    }
    table = pd.DataFrame({LABELS[p]: [fn(comparison[p]) for fn in rows.values()]
                          for p in PATHWAYS}, index=rows.keys())
    table.index.name = "Criteria"
    st.table(table)
    st.caption("Ranges are planning scenarios, not statistical confidence intervals. The methane avoided is the same across pathways because the same food is diverted; net GHG differs by processing method.")


def range_text(value, digits=0):
    return (f"{value['base']:,.{digits}f} "
            f"({value['low']:,.{digits}f}–{value['high']:,.{digits}f})")


def evidence():
    st.caption("All calculations use documented assumptions with source links and confidence ranges.")
    with st.expander("All numbers and sources"):
        data = pd.read_csv(DATA / "assumptions.csv")
        data.insert(0, "Source link", data["source_url"].fillna("").str.split(";").str[0])
        st.dataframe(
            data[["item", "unit", "min", "base", "max", "confidence",
                  "source_id", "Source link", "source_url", "notes", "key"]],
            hide_index=True, width="stretch",
            column_config={"Source link": st.column_config.LinkColumn("Source link")},
        )
        st.caption("Confidence: H = direct evidence; M = modelled or vendor data; L = team assumption. Multiple URLs are retained in the source_url column.")


def methodology():
    st.write("The planner checks NSW mandate timing from general-waste bin capacity, compares three pathways, sizes a collection plan, and projects the same conditions to 2035.")
    with st.expander("Detailed recommendation rules"):
        st.markdown(f"""
| Rule | Condition | Result |
|---|---|---|
| R0 | Default | Off-site FOGO |
| R1 | On-site space under {v(CFG, 'space_moderate_min_m2'):g} m² | Hybrid and On-site excluded |
| R2 | Food waste ≥ {v(CFG, 't1_hybrid_kg_week'):,.0f} kg/week, space ≥ {v(CFG, 'space_moderate_min_m2'):g} m², local use, Medium or High budget | Hybrid candidate |
| R3 | Food waste ≥ {v(CFG, 't2_onsite_kg_week'):,.0f} kg/week, space ≥ {v(CFG, 'space_ample_min_m2'):g} m², High budget | On-site candidate |
| R4 | On-site candidate but no local use | Off-site FOGO |
| R5 | Off-site needs {v(CFG, 'r5_high_collections_per_week'):g}+ collections/week and Hybrid needs fewer | Advisory note |
""")
        st.caption("The volume and space thresholds are planning rules, not laws or break-even points. The mandate check is indicative and does not model exemptions.")
    evidence()


def scroll_to_top():
    """Return to the answer after switching from the longer input screen."""
    if hasattr(st, "html") and "unsafe_allow_javascript" in inspect.signature(st.html).parameters:
        st.html(
            "<script>document.querySelector('section.stMain')?.scrollTo(0, 0)</script>",
            unsafe_allow_javascript=True,
        )
    else:
        components.html(
            "<script>window.parent.document.querySelector('section.stMain')?.scrollTo(0, 0)</script>",
            height=0,
        )


def pathway_summary(pathway):
    return {
        "offsite": "Separate captured food waste and send it to an off-site composting service.",
        "hybrid": "Process part of the captured food waste on site and send the remainder to off-site FOGO.",
        "onsite": "Process most captured food waste on site, with FOGO collection for the remainder.",
    }[pathway]


def overview_tab(result):
    rec, plan = result["recommendation"], result["plan"]
    st.markdown('<div class="eyebrow">Recommended pathway</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="pathway">{rec["label"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="result-note">{pathway_summary(rec["pathway"])}</div>',
                unsafe_allow_html=True)
    st.caption(f"{result['building_name'] or 'Your building'} · "
               f"{result['waste_profile']['total_kg_week']:,.0f} kg food waste/week")
    mandate_banner(result["mandate"])

    st.subheader("Your plan at a glance")
    a, b, c = st.columns(3)
    a.metric("Processed on site", f"{plan['onsite_kg_week']:,.0f} kg/week")
    b.metric("Sent off site", f"{plan['offsite_kg_week']:,.0f} kg/week")
    c.metric("Methane avoided", f"{plan['ch4_avoided_kg_year']['base']:,.0f}")
    c.caption("kg CH₄/year")
    a, b = st.columns(2)
    a.metric("FOGO bins", f"{plan['bins']} × {plan['bin_size_l']} L")
    b.metric("Collections", f"{plan['collections_per_week']} per week")

    st.subheader("Why this pathway")
    st.markdown("\n".join(f"- {reason}" for reason in rec["reasons"][:3]))
    if rec["r5_note"]:
        st.info(rec["r5_note"])
    with st.expander("What could change this recommendation?"):
        st.write(rec["what_would_change"])
        for pathway, reasons in rec["rejected"].items():
            st.caption(f"{LABELS[pathway]}: {'; '.join(reasons)}")
    if rec["warnings"]:
        with st.expander("Warnings and site checks"):
            for warning in rec["warnings"]:
                st.warning(warning)


def plan_tab(result):
    plan = result["plan"]
    st.header("Put the recommendation into practice")
    st.subheader("Waste allocation")
    a, b, c = st.columns(3)
    a.metric("Generated", f"{result['waste_profile']['total_kg_week']:,.0f} kg/week")
    b.metric("Processed on site", f"{plan['onsite_kg_week']:,.0f} kg/week")
    c.metric("Sent off site", f"{plan['offsite_kg_week']:,.0f} kg/week")

    st.subheader("Collection setup")
    st.write(f"**{plan['bins']} × {plan['bin_size_l']} L FOGO bins**, collected "
             f"**{plan['collections_per_week']} times per week**.")
    st.write("Collection days: " + (" · ".join(plan["collection_days"]) or "None"))
    st.caption(f"{plan['lifts_per_week']} bin lifts/week · indicative cost "
               f"${plan['collection_cost_aud_week']:,.0f}/week ex GST")
    if plan["local_use_line"]:
        st.success(plan["local_use_line"])

    st.subheader("Next steps")
    st.markdown("\n".join(f"{index}. {step}" for index, step in enumerate(plan["next_steps"], 1)))

    future = next(row for row in result["roadmap"]["rows"] if row["year"] == 2035)
    st.subheader("Build for 2035")
    st.info(f"At a projected {future['food_waste_kg_week']:,.0f} kg/week in 2035, "
            f"the recommended pathway is **{future['pathway']}**.")
    with st.expander("View detailed 2035 projection"):
        roadmap = pd.DataFrame(result["roadmap"]["rows"])
        st.line_chart(roadmap.set_index("year")[["food_waste_kg_week"]])
        st.dataframe(roadmap, hide_index=True, width="stretch")
        cumulative = result["roadmap"]["cumulative_net_ghg_t_2026_2035"]
        st.caption(f"Indicative net GHG saving, 2026–2035: {range_text(cumulative, 1)} t CO₂e. "
                   f"{result['roadmap']['note']}")


def evidence_tab(result):
    rec = result["recommendation"]
    st.header("Compare and verify")
    st.write("A concise comparison first; technical calculations and sources remain available below.")
    simple_comparison(result)
    with st.expander("View full technical comparison"):
        full_comparison(result, st.session_state.inputs["local_use"])
        chosen = result["comparison"][rec["pathway"]]
        st.caption(f"Of {result['waste_profile']['total_kg_week']:,.0f} kg/week generated, "
                   f"{chosen['captured_kg_week']:,.0f} kg/week is expected to be separated and "
                   f"{chosen['uncaptured_kg_week']:,.0f} kg/week remains uncaptured.")
    mandate_details(result["mandate"])
    profile = result["waste_profile"]
    if profile["tenants"]:
        with st.expander("View waste by tenant"):
            table = pd.DataFrame(profile["tenants"])
            st.dataframe(table[["name", "size", "count", "kg_week", "estimated"]],
                         hide_index=True, width="stretch")
            if any(t["estimated"] for t in profile["tenants"]):
                st.caption("Estimated tenant volumes use illustrative values from the assumptions sheet.")
    st.subheader("Methodology & evidence")
    methodology()


def results_page(result):
    if st.session_state.pop("scroll_to_result", False):
        scroll_to_top()
    top_left, top_right = st.columns([4, 1])
    top_left.markdown('<div class="eyebrow">Circular Organics Planner</div>', unsafe_allow_html=True)
    if top_right.button("← Edit inputs"):
        st.session_state.show_results = False
        st.session_state.input_step = "waste"
        st.rerun()
    overview, plan, evidence_view = st.tabs(["Overview", "Plan", "Evidence"])
    with overview:
        overview_tab(result)
    with plan:
        plan_tab(result)
    with evidence_view:
        evidence_tab(result)


def about_page():
    st.markdown('<div class="eyebrow">About</div>', unsafe_allow_html=True)
    st.title("A practical first step for building food waste.")
    st.markdown(
        '<div class="lead">The planner helps managers of NSW buildings with shared food services '
        'choose a workable organics pathway before seeking quotes or approvals.</div>',
        unsafe_allow_html=True,
    )
    st.subheader("Three pathways")
    st.markdown("""
**Off-site FOGO**

Separate food waste and have it collected for off-site composting.

**Hybrid**

Process part on site and send the remainder to off-site FOGO.

**On-site**

Process most captured food waste on site, with a service for the remainder.
""")
    st.subheader("Clear reasoning")
    st.write("The recommendation uses visible rules for waste volume, space, local output use, and budget. Every assumption and source remains available in the Evidence tab after running a plan.")
    st.caption("Built for Climate Hack-tion 2026 · Build for 2035. Planning guidance only; confirm legal duties with NSW EPA or your council.")


initialise_state()
page = st.sidebar.radio("Menu", ["Planner", "About"])
st.sidebar.caption("NSW food-waste decision tool")
if page == "About":
    about_page()
elif st.session_state.show_results and "result" in st.session_state:
    results_page(st.session_state.result)
else:
    input_page()
