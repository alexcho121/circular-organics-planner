"""Streamlit interface for the Circular Organics Planner.

All planning decisions and calculated values come from app.engine.
"""
import json
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
        "show_results": False, "editor_version": 0,
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
        "editor_version": st.session_state.editor_version + 1,
        "show_results": False,
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


def input_page():
    st.title("Circular Organics Planner")
    st.write(
        "Find a practical food-waste pathway for your NSW building. Compare Off-site FOGO, "
        "Hybrid, and On-site; get a plan and an estimate of landfill methane avoided."
    )
    st.caption("Start with five essentials. You can refine the building profile later.")

    demo_a, demo_b = st.columns(2)
    if demo_a.button("Try a small cafe building", width="stretch"):
        load_example("case_1_small_cafe_building")
        st.rerun()
    if demo_b.button("Try a shopping centre food court", width="stretch"):
        load_example("case_2_shopping_centre_food_court")
        st.rerun()
    st.caption("Examples are illustrative.")

    version = st.session_state.editor_version
    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("Food waste")
        st.number_input(
            "Food waste (kg/week)", min_value=0.0, step=10.0, key="total_kg",
            help="Use a weighed figure if available. Leave at zero to estimate from tenants below.",
        )
        st.subheader("General waste bins")
        st.caption("Include landfill bins only. Bin size, count, and collection frequency determine the NSW mandate status.")
        bins = st.data_editor(
            st.session_state.bins_df, key=f"bins_{version}", num_rows="dynamic",
            width="stretch",
            column_config={
                "Bin size (L)": st.column_config.SelectboxColumn(
                    options=[120, 240, 360, 660, 1100], required=True),
                "Count": st.column_config.NumberColumn(min_value=0, step=1, required=True),
                "Collections/week": st.column_config.NumberColumn(
                    min_value=0, max_value=14, step=1, required=True),
            },
        )
    with right:
        st.subheader("On-site fit")
        st.number_input("Available space for on-site processing (m²)", min_value=0.0,
                        step=1.0, key="space_m2")
        st.radio("Local use for processed output?", ["Yes", "No"], horizontal=True,
                 key="local_use", help="For example, landscaping or a processor contract.")
        st.selectbox("Budget for on-site equipment", ["low", "medium", "high"],
                     format_func=lambda key: f"{key.title()}: {BUDGET_LABELS[key]}", key="budget")

    with st.expander("Don't know your weekly food waste? Estimate from tenants"):
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

    if st.button("Compare my options", type="primary"):
        inputs = collect_inputs(tenants, bins)
        if waste_profile(inputs, CFG)["total_kg_week"] <= 0:
            st.error("Enter weekly food waste or add at least one tenant estimate.")
        else:
            st.session_state.update({
                "inputs": inputs, "result": plan_building(inputs, CFG),
                "tenants_df": tenants, "bins_df": bins,
                "show_results": True, "editor_version": version + 1,
                "scroll_to_result": True,
            })
            st.rerun()


def mandate_banner(mandate):
    if mandate["status_code"] == "unknown":
        st.info(mandate["status_text"])
        return
    message = (f"**NSW FOGO status: {mandate['status_text']}** · "
               f"general-waste capacity {mandate['capacity_l_week']:,.0f} L/week")
    (st.warning if mandate["status_code"] == "covered_2026" else st.info)(message)
    with st.expander("NSW mandate details and exemptions"):
        st.markdown("\n".join(f"- {note}" for note in mandate["notes"]))


def comparison_cards(result):
    columns = st.columns(3, gap="medium")
    for column, pathway in zip(columns, PATHWAYS):
        item = result["comparison"][pathway]
        with column:
            with st.container(border=True):
                title = LABELS[pathway]
                if pathway == result["recommendation"]["pathway"]:
                    title += " · Recommended"
                st.markdown(f"**{title}**")
                st.write(f"{item['onsite_kg_week']:,.0f} kg on-site / {item['offsite_kg_week']:,.0f} kg off-site per week")
                st.caption(f"Space: {item['space']} · Effort: {item['effort']}")
                bin_word = "bin" if item["bins"] == 1 else "bins"
                st.write(f"{item['bins']} {bin_word} · {item['collections_per_week']} collections/week")
                st.write(f"Collection: ${item['collection_cost_aud_week']:,.0f}/week (indicative)")
                st.caption(f"Landfill methane avoided: {item['ch4_avoided_kg_year']['base']:,.0f} kg CH₄/year")
                st.caption(f"Net GHG saving: {item['net_ghg_t_year']['base']:,.1f} t CO₂e/year")


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


def results_page(result):
    rec, plan = result["recommendation"], result["plan"]
    if st.session_state.pop("scroll_to_result", False):
        components.html(
            "<script>window.parent.document.querySelector('section.stMain')?.scrollTo(0, 0)</script>",
            height=0,
        )
    with st.container(border=True):
        st.caption("YOUR RECOMMENDATION")
        st.header(rec["label"])
        st.write(f"For {result['building_name'] or 'your building'} · {result['waste_profile']['total_kg_week']:,.0f} kg food waste/week")
    mandate_banner(result["mandate"])

    st.subheader("What the plan looks like")
    a, b, c = st.columns(3)
    a.metric("Processed on-site", f"{plan['onsite_kg_week']:,.0f} kg/week")
    b.metric("Sent to off-site FOGO", f"{plan['offsite_kg_week']:,.0f} kg/week")
    c.metric("Landfill methane avoided", f"{plan['ch4_avoided_kg_year']['base']:,.0f}")
    c.caption("kg CH₄/year · planning range "
              f"{plan['ch4_avoided_kg_year']['low']:,.0f}–{plan['ch4_avoided_kg_year']['high']:,.0f}")
    a, b = st.columns(2)
    a.metric("Food-waste bins", f"{plan['bins']} × {plan['bin_size_l']} L")
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

    st.subheader("Compare your options")
    comparison_cards(result)
    with st.expander("View full technical comparison"):
        full_comparison(result, st.session_state.inputs["local_use"])
        chosen = result["comparison"][rec["pathway"]]
        st.caption(f"Of {result['waste_profile']['total_kg_week']:,.0f} kg/week generated, "
                   f"{chosen['captured_kg_week']:,.0f} kg/week is expected to be separated "
                   f"and {chosen['uncaptured_kg_week']:,.0f} kg/week remains uncaptured.")

    st.subheader("Implementation plan")
    st.markdown("\n".join(f"{index}. {step}" for index, step in enumerate(plan["next_steps"], 1)))
    st.caption(f"Collection days: {' · '.join(plan['collection_days']) or 'none'} · "
               f"{plan['lifts_per_week']} bin lifts/week · indicative collection cost "
               f"${plan['collection_cost_aud_week']:,.0f}/week (ex GST).")
    if plan["local_use_line"]:
        st.info(plan["local_use_line"])

    future = next(row for row in result["roadmap"]["rows"] if row["year"] == 2035)
    st.subheader("Build for 2035")
    st.write(f"At a projected {future['food_waste_kg_week']:,.0f} kg/week in 2035, the recommended pathway is **{future['pathway']}**.")
    with st.expander("View 2035 projection"):
        roadmap = pd.DataFrame(result["roadmap"]["rows"])
        st.line_chart(roadmap.set_index("year")[["food_waste_kg_week"]])
        st.dataframe(roadmap, hide_index=True, width="stretch")
        cumulative = result["roadmap"]["cumulative_net_ghg_t_2026_2035"]
        st.caption(f"Indicative net GHG saving, 2026–2035: {range_text(cumulative, 1)} t CO₂e. {result['roadmap']['note']}")

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
    if st.button("Edit building inputs"):
        st.session_state.show_results = False
        st.rerun()


def about_page():
    st.title("About the planner")
    st.write("Built for Climate Hack-tion 2026, Build for 2035. For managers of NSW buildings where food tenants share a waste service.")
    st.subheader("How it works")
    st.markdown("1. Profile your waste stream\n2. Compare Off-site FOGO, Hybrid, and On-site\n3. Get a recommended implementation plan")
    st.subheader("Methodology & evidence")
    methodology()
    st.caption("Planning guidance only. Confirm mandate duties with NSW EPA or your council; check approvals and quotes before buying equipment.")


initialise_state()
page = st.sidebar.radio("Menu", ["Planner", "About"])
st.sidebar.caption("Circular Organics Planner · illustrative prototype")
if page == "About":
    about_page()
elif st.session_state.show_results and "result" in st.session_state:
    results_page(st.session_state.result)
else:
    input_page()
