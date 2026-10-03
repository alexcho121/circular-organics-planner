"""Streamlit interface for the Circular Organics Planner.

All planning decisions and calculated values come from app.engine.
"""
import json
import inspect
import sys
from html import escape
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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Manrope:wght@500;600;700;800&display=swap');
    #MainMenu, footer {visibility: hidden;}
    header[data-testid="stHeader"] {background: transparent;}
    [data-testid="stSidebar"] {display: none;}
    .stApp {background: #0F1318; color: #F4F6F8; font-family: Inter, Arial, sans-serif;}
    .stMainBlockContainer {max-width: 1120px; padding-top: 1.35rem; padding-bottom: 4.5rem;}
    h1, h2, h3 {font-family: Manrope, Inter, Arial, sans-serif; letter-spacing: -.035em; color: #F4F6F8;}
    h1 {font-size: clamp(2.6rem, 4.7vw, 4.35rem); line-height: 1.05; margin-bottom: .7rem;}
    h2 {font-size: 1.55rem; margin-top: 1.9rem;}
    h3 {font-size: 1.05rem; letter-spacing: -.015em;}
    p, li {color: #A9B0B8; line-height: 1.6;}
    hr {border-color: #2A313A; margin: 2.25rem 0;}
    .eyebrow {color:#A9B0B8; font-family: Manrope, Inter, sans-serif; font-size:.72rem; font-weight:800; letter-spacing:.14em; text-transform:uppercase;}
    .plan-eyebrow {color:#B89B5E; font-family: Manrope, Inter, sans-serif; font-size:.72rem; font-weight:800; letter-spacing:.14em; text-transform:uppercase;}
    .lead {font-size:1.12rem; line-height:1.65; max-width:760px; color:#A9B0B8;}
    .brand {font-family: Manrope, Inter, sans-serif; font-weight:800; font-size:1rem; color:#F4F6F8; letter-spacing:-.025em; padding:.48rem 0 1.25rem;}
    .section-label {color:#A9B0B8; font-family:Manrope, Inter, sans-serif; font-size:.72rem; font-weight:800; letter-spacing:.14em; text-transform:uppercase; margin:2.3rem 0 .75rem;}
    .stButton > button {border-radius:9px; border-color:#3A424C; background:#1D232B; color:#F4F6F8; font-family:Manrope, Inter, sans-serif; font-weight:700; min-height:2.7rem;}
    .stButton > button[kind="primary"] {background:#23865B; border-color:#23865B; color:#F4F6F8; min-height:3.1rem; min-width:232px; padding:.65rem 1.35rem;}
    .stButton > button[kind="primary"]:hover {background:#2C9A69; border-color:#2C9A69;}
    .stButton > button[kind="secondary"] {background:transparent; color:#A9B0B8; border-color:transparent;}
    .st-key-load_example_button button {background:#1D232B !important; border-color:#3A424C !important; color:#F4F6F8 !important; min-height:2.55rem !important;}
    .st-key-load_example_button button:hover {background:#252C35 !important; border-color:#4A5561 !important;}
    div[data-baseweb="input"], div[data-baseweb="select"] > div {border-color:#2A313A; border-radius:8px; background:#171C22; color:#F4F6F8; min-height:3rem;}
    [data-testid="stWidgetLabel"] p {font-size:.92rem; font-weight:500; color:#F4F6F8;}
    div[data-baseweb="select"] span, div[data-baseweb="select"] svg {color:#F4F6F8; fill:#F4F6F8;}
    [data-testid="stNumberInput"] button {display:none;}
    [data-testid="stNumberInput"] input {color:#F4F6F8; font-variant-numeric:tabular-nums;}
    [data-testid="stDataFrame"], [data-testid="stDataEditor"] {border:1px solid #2A313A; border-radius:8px; overflow:hidden;}
    [data-testid="stExpander"] {background:transparent; border:0; border-radius:0;}
    [data-testid="stExpander"] details {background:transparent !important; border:0 !important; border-radius:0 !important;}
    [data-testid="stExpander"] summary {color:#A9B0B8; font-size:.86rem; padding:0 !important;}
    [data-testid="stCheckbox"] {margin-top:.1rem;}
    [data-testid="stCheckbox"] label {font-size:.78rem; color:#737B85;}
    [data-testid="stAlert"] {border-radius:8px; background:#171C22; border-color:#2A313A;}
    .pathway {font-family:Manrope, Inter, sans-serif; font-size:clamp(3rem, 6.2vw, 5.1rem); line-height:.95; color:#F4F6F8; font-weight:800; letter-spacing:-.07em; margin:.35rem 0 .8rem;}
    .result-note {font-size:1.08rem; line-height:1.55; color:#A9B0B8; max-width:520px;}
    .status {border-left:2px solid #23865B; padding:.2rem 0 .2rem .85rem; margin-top:1.45rem; color:#A9B0B8; font-size:.9rem; line-height:1.45;}
    .status strong {color:#2C9A69;}
    .allocation {margin:1.1rem 0 1.8rem; max-width:760px;}
    .allocation-labels {display:flex; justify-content:space-between; gap:1rem; color:#A9B0B8; font-size:.83rem; margin-bottom:.55rem;}
    .allocation-labels strong {color:#F4F6F8; font-family:Manrope, Inter, sans-serif;}
    .allocation-bar {display:flex; height:12px; border-radius:99px; overflow:hidden; background:#2A313A;}
    .allocation-onsite {background:#23865B;}.allocation-offsite {background:#B89B5E;}
    .stat {border-top:1px solid #2A313A; padding-top:.8rem; margin-top:.25rem;}
    .stat-label {font-size:.76rem; color:#737B85; text-transform:uppercase; letter-spacing:.08em; font-weight:700;}
    .stat-value {font-family:Manrope, Inter, sans-serif; font-variant-numeric:tabular-nums; color:#F4F6F8; font-size:1.55rem; font-weight:800; letter-spacing:-.04em; margin:.12rem 0;}
    .stat-detail {font-size:.85rem; color:#A9B0B8;}
    .climate {border-left:2px solid #23865B; padding:.25rem 0 .25rem 1.25rem; margin:2rem 0 .7rem;}
    .climate-value {font-family:Manrope, Inter, sans-serif; font-variant-numeric:tabular-nums; color:#F4F6F8; font-size:clamp(2.8rem, 5vw, 4.2rem); line-height:1; font-weight:800; letter-spacing:-.065em; margin:.35rem 0;}
    .reason {display:flex; gap:.7rem; align-items:flex-start; border-top:1px solid #2A313A; padding:.85rem 0; color:#A9B0B8; max-width:760px;}
    .check {color:#2C9A69; font-family:Manrope, Inter, sans-serif; font-weight:800;}
    .path-status {display:flex; justify-content:space-between; border-top:1px solid #2A313A; padding:.7rem 0; font-size:.92rem;}
    .path-status strong {font-family:Manrope, Inter, sans-serif; color:#F4F6F8;}
    .path-status span {color:#A9B0B8;}
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
        "show_results": False, "view": "planner", "editor_version": 0,
        "multiple_bin_types": False, "bin_size": 240, "bin_count": 2,
        "bin_collections": 2, "food_waste_entry": "I know the amount",
        "demo_loaded": None,
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
        "show_results": False, "view": "planner", "food_waste_entry": "I know the amount",
        "demo_loaded": key,
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
    with st.expander("Try a demo →"):
        choice = st.selectbox(
            "Example building",
            ["case_1_small_cafe_building", "case_2_shopping_centre_food_court"],
            format_func=lambda key: ("Small café" if key.startswith("case_1")
                                     else "Shopping centre food court"),
            label_visibility="collapsed",
        )
        st.button("Load example", key="load_example_button", on_click=load_example, args=(choice,))
    if st.session_state.demo_loaded:
        label = "Small café" if st.session_state.demo_loaded.startswith("case_1") else "Shopping centre"
        st.caption(f"{label} example loaded — all values can still be edited.")


def planner_workspace():
    st.markdown('<div class="section-label">Waste service</div>', unsafe_allow_html=True)
    st.subheader("Food waste")
    entry_mode = st.radio("Food waste entry", ["I know the amount", "Estimate it"], horizontal=True,
                          key="food_waste_entry", label_visibility="collapsed")
    version = st.session_state.editor_version
    tenants = st.session_state.tenants_df
    if entry_mode == "I know the amount":
        waste_input, unit, _ = st.columns([1, .45, 2.75])
        with waste_input:
            st.number_input("Weekly food waste", min_value=0.0, step=10.0, format="%.0f", key="total_kg")
        unit.markdown('<div style="padding-top:2.4rem;color:#A9B0B8;font-size:.9rem">kg/week</div>', unsafe_allow_html=True)
    else:
        st.caption("Estimate weekly food waste from the tenant mix.")
        tenants = st.data_editor(st.session_state.tenants_df, key=f"tenants_{version}", num_rows="dynamic", width="stretch", column_config={
            "Tenant": st.column_config.TextColumn(required=True),
            "Type": st.column_config.SelectboxColumn(options=list(TENANT_TYPES.values()), required=True),
            "Size": st.column_config.SelectboxColumn(options=["Small", "Medium", "Large"], required=True),
            "Count": st.column_config.NumberColumn(min_value=1, step=1, required=True),
            "Measured kg/week": st.column_config.NumberColumn(min_value=0, help="Optional weighed amount; replaces the type estimate."),
        })

    st.subheader("General waste service", help="Used to check when NSW FOGO requirements are likely to apply.")
    a, b, c, _ = st.columns([1, 1, 1, 1.2])
    a.selectbox("Bin size", [120, 240, 360, 660, 1100], key="bin_size", help="Used to check your likely NSW FOGO requirement.",
                format_func=lambda value: f"{value} L")
    b.number_input("Number of bins", min_value=1, step=1, key="bin_count")
    c.number_input("Collections per week", min_value=1, max_value=14, step=1,
                   key="bin_collections")

    st.checkbox("+ Add another bin type", key="multiple_bin_types")
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

    st.markdown('<div class="section-label">On-site capability</div>', unsafe_allow_html=True)
    a, b, c, _ = st.columns([1, 1.35, 1, 1.15])
    a.number_input("On-site space (m²)", min_value=0.0, step=1.0, format="%.0f", key="space_m2")
    b.radio("Local use", ["Yes", "No"], horizontal=True, key="local_use", help="Can processed material be used on site or nearby?")
    c.radio("Budget", ["low", "medium", "high"], horizontal=True,
            format_func=str.title, key="budget")

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
    if st.button("Compare pathways →", type="primary"):
        inputs = collect_inputs(tenants, bins)
        if entry_mode == "Estimate it":
            inputs["total_food_waste_kg_week"] = None
        if waste_profile(inputs, CFG)["total_kg_week"] <= 0:
            st.error("Enter weekly food waste or add at least one tenant estimate.")
            return
        st.session_state.update({
            "inputs": inputs, "result": plan_building(inputs, CFG),
            "bins_df": bins, "show_results": True,
            "editor_version": st.session_state.editor_version + 1,
            "scroll_to_result": True,
        })
        st.rerun()


def input_page():
    st.markdown('<div class="plan-eyebrow">Plan your food waste</div>', unsafe_allow_html=True)
    st.markdown("<h1>Find the right setup<br>for your building.</h1>", unsafe_allow_html=True)
    st.caption("Off-site FOGO · Hybrid · On-site")
    planner_workspace()
    example_picker()


def mandate_status(mandate):
    return f'<div class="status"><strong>NSW FOGO ●</strong><br>{escape(mandate["status_text"])}</div>'


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


def outlook_copy(result):
    future = next(row for row in result["roadmap"]["rows"] if row["year"] == 2035)
    current_pathway = result["recommendation"]["label"]
    if current_pathway == future["pathway"]:
        return f"{current_pathway} remains suitable at the projected {future['food_waste_kg_week']:,.0f} kg/week."
    return (f"The recommended pathway moves from {current_pathway} to {future['pathway']} by 2035 "
            f"at the projected {future['food_waste_kg_week']:,.0f} kg/week.")


def next_step_copy(plan):
    if plan["pathway"] == "offsite":
        return (f"Set up {plan['bins']} × {plan['bin_size_l']} L FOGO bins with "
                f"{plan['collections_per_week']} collections per week.")
    if plan["pathway"] == "hybrid":
        return (f"Process {plan['onsite_kg_week']:,.0f} kg/week on site and send the remaining "
                f"{plan['offsite_kg_week']:,.0f} kg/week through FOGO.")
    return (f"Prepare the site to process {plan['onsite_kg_week']:,.0f} kg/week on site and send "
            f"the remaining {plan['offsite_kg_week']:,.0f} kg/week through FOGO.")


def overview_tab(result):
    rec, plan = result["recommendation"], result["plan"]
    hero, status = st.columns([3, 1], gap="large")
    with hero:
        st.markdown('<div class="plan-eyebrow">Your plan</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="pathway">{escape(rec["label"])}</div>', unsafe_allow_html=True)
        st.caption("Recommended pathway")
        st.markdown(f'<div class="result-note">{pathway_summary(rec["pathway"])}</div>', unsafe_allow_html=True)
    with status:
        st.markdown(mandate_status(result["mandate"]), unsafe_allow_html=True)

    total = plan["onsite_kg_week"] + plan["offsite_kg_week"]
    onsite_pct = (plan["onsite_kg_week"] / total * 100) if total else 0
    st.markdown('<div class="eyebrow">Waste allocation</div>', unsafe_allow_html=True)
    st.markdown(f'''<div class="allocation"><div class="allocation-labels"><span><strong>{plan['onsite_kg_week']:,.0f} kg/week</strong><br>processed on site</span><span style="text-align:right"><strong>{plan['offsite_kg_week']:,.0f} kg/week</strong><br>sent off site</span></div><div class="allocation-bar"><div class="allocation-onsite" style="width:{onsite_pct:.2f}%"></div><div class="allocation-offsite" style="width:{100-onsite_pct:.2f}%"></div></div></div>''', unsafe_allow_html=True)

    st.markdown('<div class="eyebrow">Operation</div>', unsafe_allow_html=True)
    bins, collections = st.columns(2)
    bins.markdown(f'<div class="stat"><div class="stat-label">FOGO bins</div><div class="stat-value">{plan["bins"]} × {plan["bin_size_l"]} L</div><div class="stat-detail">planned container service</div></div>', unsafe_allow_html=True)
    collections.markdown(f'<div class="stat"><div class="stat-label">Collections</div><div class="stat-value">{plan["collections_per_week"]}/week</div><div class="stat-detail">{" · ".join(plan["collection_days"])}</div></div>', unsafe_allow_html=True)

    methane = plan["ch4_avoided_kg_year"]
    st.markdown(f'<div class="climate"><div class="eyebrow">Climate impact</div><div class="climate-value">{methane["base"]:,.0f}</div><div>kg CH₄/year of landfill methane avoided under the planning scenario.</div></div>', unsafe_allow_html=True)
    with st.expander("View climate assumptions"):
        st.write(f"Planning range: **{range_text(methane)} kg CH₄/year**. The range reflects the low, base and high values in the evidence sheet.")

    st.subheader(f"Why {rec['label']}")
    st.markdown("".join(f'<div class="reason"><span class="check">✓</span><span>{escape(reason)}</span></div>' for reason in rec["reasons"][:3]), unsafe_allow_html=True)
    st.markdown('<div class="section-label">Next step</div>', unsafe_allow_html=True)
    st.write(next_step_copy(plan))
    st.markdown(f'<div class="section-label">Looking ahead · 2035</div>', unsafe_allow_html=True)
    st.write(outlook_copy(result))
    if rec["r5_note"]:
        st.info(rec["r5_note"])
    if rec["warnings"]:
        with st.expander("Warnings and site checks"):
            for warning in rec["warnings"]:
                st.warning(warning)


def plan_tab(result):
    plan = result["plan"]
    st.subheader("Implementation plan")
    st.markdown(f"**{plan['onsite_kg_week']:,.0f} kg/week** processed on site · **{plan['offsite_kg_week']:,.0f} kg/week** sent off site")
    st.markdown("**Collection setup**")
    st.write(f"**{plan['bins']} × {plan['bin_size_l']} L FOGO bins**, collected "
             f"**{plan['collections_per_week']} times per week**.")
    st.write("Collection days: " + (" · ".join(plan["collection_days"]) or "None"))
    st.caption(f"{plan['lifts_per_week']} bin lifts/week · indicative cost "
               f"${plan['collection_cost_aud_week']:,.0f}/week ex GST")
    if plan["local_use_line"]:
        st.success(plan["local_use_line"])

    st.markdown("**Next steps**")
    st.markdown("\n".join(f"{index}. {step}" for index, step in enumerate(plan["next_steps"], 1)))

    st.markdown(f"**2035 outlook** — {outlook_copy(result)}")
    with st.expander("Explore 2035 projection →"):
        roadmap = pd.DataFrame(result["roadmap"]["rows"])
        st.line_chart(roadmap.set_index("year")[["food_waste_kg_week"]])
        st.dataframe(roadmap, hide_index=True, width="stretch")
        cumulative = result["roadmap"]["cumulative_net_ghg_t_2026_2035"]
        st.caption(f"Indicative net GHG saving, 2026–2035: {range_text(cumulative, 1)} t CO₂e. "
                   f"{result['roadmap']['note']}")


def why_recommendation(result):
    rec = result["recommendation"]
    for pathway in PATHWAYS:
        status = "Recommended" if pathway == rec["pathway"] else "Not selected"
        st.markdown(f'<div class="path-status"><strong>{escape(LABELS[pathway])}</strong><span>{status}</span></div>', unsafe_allow_html=True)
    st.write(rec["what_would_change"])
    for pathway, reasons in rec["rejected"].items():
        st.caption(f"{LABELS[pathway]}: {'; '.join(reasons)}")
    with st.expander("View full technical comparison"):
        full_comparison(result, st.session_state.inputs["local_use"])


def evidence_tab(result):
    st.header("Evidence and methodology")
    st.write("The recommendation rules, NSW mandate check and source assumptions used for this plan.")
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
    if top_right.button("← Edit inputs"):
        st.session_state.show_results = False
        st.rerun()
    overview_tab(result)
    with st.expander("View implementation plan →"):
        plan_tab(result)
    with st.expander("Why this recommendation?"):
        why_recommendation(result)
    with st.expander("Methodology & sources"):
        st.caption("All calculations use documented assumptions, source links and confidence levels.")
        mandate_details(result["mandate"])
        profile = result["waste_profile"]
        if profile["tenants"]:
            with st.expander("View waste by tenant"):
                table = pd.DataFrame(profile["tenants"])
                st.dataframe(table[["name", "size", "count", "kg_week", "estimated"]], hide_index=True, width="stretch")
        methodology()


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


def top_header():
    brand, navigation = st.columns([6, 1])
    brand.markdown('<div class="brand">Circular Organics Planner</div>', unsafe_allow_html=True)
    label = "Planner" if st.session_state.view == "about" else "Methodology"
    if navigation.button(label, key="header_navigation"):
        st.session_state.view = "planner" if st.session_state.view == "about" else "about"
        st.rerun()


initialise_state()
top_header()
if st.session_state.view == "about":
    about_page()
elif st.session_state.show_results and "result" in st.session_state:
    results_page(st.session_state.result)
else:
    input_page()
