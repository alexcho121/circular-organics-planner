"""Plain-language Streamlit UI; all recommendation logic remains in handoff.engine."""
import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT))
from app.engine import LABELS, PATHWAYS, budget_bands, load_config, plan_building, waste_profile

st.set_page_config(page_title="Circular Organics Planner", layout="wide")
CFG = load_config(DATA / "assumptions.csv")
EXAMPLES = json.loads((DATA / "examples.json").read_text())
BUDGET = budget_bands(CFG)
TYPE_LABELS = {"cafe": "Cafe", "restaurant": "Restaurant", "quick_service": "Quick service", "bakery": "Bakery", "grocery": "Grocery"}
LABEL_TO_TYPE = {v: k for k, v in TYPE_LABELS.items()}
BUILDING_TYPES = {"shopping_centre": "Shopping centre", "food_court": "Food court", "university": "University campus", "commercial_building": "Commercial building", "hospitality": "Hospitality venue"}


def tenant_frame(rows=None):
    rows = rows or [{"type": "cafe", "size": "medium", "count": 1}]
    return pd.DataFrame([{"Type": TYPE_LABELS[r["type"]], "Size": r.get("size", "medium").title(), "Count": int(r.get("count", 1)), "Measured kg/week": r.get("kg_week")} for r in rows])


def bin_frame(rows=None):
    rows = rows or [{"size_l": 240, "count": 2, "collections_per_week": 2}]
    return pd.DataFrame([{"Bin size (L)": int(r["size_l"]), "Count": int(r["count"]), "Collections/week": int(r["collections_per_week"])} for r in rows])


def init_state():
    defaults = {"building_name": "My building", "building_type": "food_court", "tenant_count": 6, "total_kg": 0.0, "current_collections": 0, "room_m2": 10.0, "space_m2": 0.0, "cost_week": 0.0, "local_use": "No", "budget": "low", "growth": 0.0, "tenants_df": tenant_frame(), "bins_df": bin_frame(), "show_results": False, "editor_version": 0}
    for key, value in defaults.items(): st.session_state.setdefault(key, value)


def load_example(key):
    ex = EXAMPLES[key]
    st.session_state.update({"building_name": ex["building_name"], "building_type": ex["building_type"], "tenant_count": sum(int(t.get("count", 1)) for t in ex.get("tenants", [])), "total_kg": float(ex.get("total_food_waste_kg_week") or 0), "current_collections": int(ex["current_collections_per_week"]), "room_m2": float(ex["waste_room_area_m2"]), "space_m2": float(ex["onsite_space_m2"]), "cost_week": float(ex.get("current_collection_cost_aud_week") or 0), "local_use": "Yes" if ex["local_use"] else "No", "budget": ex["budget_level"], "growth": float(ex.get("annual_change_pct") or 0), "tenants_df": tenant_frame(ex.get("tenants")), "bins_df": bin_frame(ex["general_waste_bins"]), "editor_version": st.session_state.editor_version + 1, "show_results": False})


def inputs_from_tables(tenants, bins):
    tenant_rows, bin_rows = [], []
    for _, r in tenants.iterrows():
        if r.get("Type") in LABEL_TO_TYPE:
            row = {"name": r["Type"], "type": LABEL_TO_TYPE[r["Type"]], "size": str(r.get("Size", "Medium")).lower(), "count": int(r.get("Count", 1))}
            if not pd.isna(r.get("Measured kg/week")): row["kg_week"] = float(r["Measured kg/week"])
            tenant_rows.append(row)
    for _, r in bins.iterrows():
        if not any(pd.isna(r.get(c)) for c in ["Bin size (L)", "Count", "Collections/week"]) and int(r["Count"]) > 0 and int(r["Collections/week"]) > 0:
            bin_rows.append({"size_l": int(r["Bin size (L)"]), "count": int(r["Count"]), "collections_per_week": int(r["Collections/week"])})
    s = st.session_state
    return {"building_name": s.building_name, "building_type": s.building_type, "number_of_food_tenants": int(s.tenant_count), "total_food_waste_kg_week": float(s.total_kg) or None, "tenants": tenant_rows, "current_collections_per_week": int(s.current_collections), "general_waste_bins": bin_rows, "waste_room_area_m2": float(s.room_m2), "onsite_space_m2": float(s.space_m2), "local_use": s.local_use == "Yes", "budget_level": s.budget, "current_collection_cost_aud_week": float(s.cost_week) or None, "annual_change_pct": float(s.growth)}


def evidence():
    st.caption("All calculations use documented assumptions with source links and confidence ranges.")
    with st.expander("All numbers and sources"):
        d = pd.read_csv(DATA / "assumptions.csv")
        st.dataframe(d[["item", "unit", "min", "base", "max", "confidence", "source_id", "source_url", "notes"]], hide_index=True, use_container_width=True, column_config={"source_url": st.column_config.LinkColumn("Source link")})


def input_page():
    st.header("Plan your food-waste service")
    st.write("Start with the essentials. Add building details when you have them.")
    c1, c2 = st.columns(2)
    if c1.button("Load Case 1: Small cafe building"): load_example("case_1_small_cafe_building"); st.rerun()
    if c2.button("Load Case 2: Shopping centre food court"): load_example("case_2_shopping_centre_food_court"); st.rerun()
    ver = st.session_state.editor_version
    left, right = st.columns(2)
    with left:
        st.number_input("Food waste (kg/week)", min_value=0.0, step=10.0, key="total_kg", help="Leave at 0 to estimate from tenants.")
        st.subheader("General waste bins")
        st.caption("Landfill bins only — required for the NSW mandate check.")
        bins = st.data_editor(st.session_state.bins_df, key=f"bins_{ver}", num_rows="dynamic", use_container_width=True, column_config={"Bin size (L)": st.column_config.SelectboxColumn(options=[120, 240, 360, 660, 1100], required=True), "Count": st.column_config.NumberColumn(min_value=0, step=1, required=True), "Collections/week": st.column_config.NumberColumn(min_value=0, max_value=14, step=1, required=True)})
    with right:
        st.number_input("Available space for on-site processing (m²)", min_value=0.0, step=1.0, key="space_m2")
        st.radio("Is there a local use for processed output?", ["Yes", "No"], horizontal=True, key="local_use")
        st.selectbox("Budget", ["low", "medium", "high"], format_func=lambda x: f"{x.title()}: {BUDGET[x]}", key="budget")
    with st.expander("Don't know your weekly food waste? Estimate from tenants", expanded=st.session_state.total_kg == 0):
        tenants = st.data_editor(st.session_state.tenants_df, key=f"tenants_{ver}", num_rows="dynamic", use_container_width=True, column_config={"Type": st.column_config.SelectboxColumn(options=list(TYPE_LABELS.values()), required=True), "Size": st.column_config.SelectboxColumn(options=["Small", "Medium", "Large"], required=True), "Count": st.column_config.NumberColumn(min_value=1, step=1, required=True), "Measured kg/week": st.column_config.NumberColumn(min_value=0)})
        st.caption("A measured seven-day audit is more reliable than an estimate.")
    with st.expander("Advanced details"):
        a, b, c = st.columns(3)
        a.text_input("Building name", key="building_name"); b.selectbox("Building type", list(BUILDING_TYPES), format_func=BUILDING_TYPES.get, key="building_type"); c.number_input("Number of food tenants", min_value=0, step=1, key="tenant_count")
        a.number_input("Current organics collections/week", min_value=0, max_value=14, step=1, key="current_collections"); b.number_input("Current collection cost (AUD/week)", min_value=0.0, step=10.0, key="cost_week"); c.number_input("Waste room area (m²)", min_value=0.0, step=1.0, key="room_m2")
        a.slider("Expected annual food-waste growth (%)", -5.0, 10.0, step=0.5, key="growth")
    if st.button("Get my recommendation", type="primary"):
        inputs = inputs_from_tables(tenants, bins)
        if waste_profile(inputs, CFG)["total_kg_week"] <= 0: st.error("Enter food waste, or add at least one tenant.")
        else:
            st.session_state.update({"inputs": inputs, "result": plan_building(inputs, CFG), "tenants_df": tenants, "bins_df": bins, "show_results": True, "editor_version": ver + 1}); st.rerun()


def mandate_banner(m):
    if m["status_code"] == "unknown": st.info(m["status_text"]); return
    msg = f"**NSW FOGO status: {m['status_text']}**  \nGeneral-waste capacity: {m['capacity_l_week']:,.0f} L/week"
    (st.warning if m["status_code"] == "covered_2026" else st.info)(msg)
    with st.expander("Regulation details and exemptions"): st.markdown("\n".join(f"- {n}" for n in m["notes"]))


def comparison(result):
    rec, rows = result["recommendation"], []
    for p in PATHWAYS:
        x = result["comparison"][p]
        rows.append({"Pathway": LABELS[p] + (" ✓" if p == rec["pathway"] else ""), "Waste split": f"{x['onsite_kg_week']:,.0f} kg on-site / {x['offsite_kg_week']:,.0f} kg off-site", "Space fit": x["space"], "Collections": f"{x['collections_per_week']}/week", "Cost": f"{x['cost']} · ${x['collection_cost_aud_week']:,.0f}/week", "Effort": x["effort"], "Methane avoided": f"{x['ch4_avoided_kg_year']['base']:,.0f} kg CH₄/year"})
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    with st.expander("View full technical comparison"):
        full = []
        for p in PATHWAYS:
            x = result["comparison"][p]
            full.append({"Pathway": LABELS[p], "Bins": f"{x['bins']} × {x['bin_size_l']} L", "Bin lifts/week": x["lifts_per_week"], "Off-site kg/week": x["offsite_kg_week"], "On-site kg/week": x["onsite_kg_week"], "Net GHG t CO₂e/year": x["net_ghg_t_year"]["base"], "Methane range kg CH₄/year": f"{x['ch4_avoided_kg_year']['low']:,.0f}–{x['ch4_avoided_kg_year']['high']:,.0f}", "Equipment budget": "None" if not x["equipment_budget"] else f"${x['equipment_budget']['min']:,.0f}–${x['equipment_budget']['max']:,.0f}"})
        st.dataframe(pd.DataFrame(full), hide_index=True, use_container_width=True)


def results_page(r):
    rec, plan = r["recommendation"], r["plan"]
    st.header(f"Recommended pathway: {rec['label']}")
    mandate_banner(r["mandate"])
    st.subheader("Your key plan metrics")
    a, b, c, d, e = st.columns(5)
    a.metric("Processed on-site", f"{plan['onsite_kg_week']:,.0f} kg/week"); b.metric("Sent to off-site FOGO", f"{plan['offsite_kg_week']:,.0f} kg/week"); c.metric("Bins", f"{plan['bins']} × {plan['bin_size_l']} L"); d.metric("Collections", f"{plan['collections_per_week']} / week")
    e.metric("Landfill methane avoided", f"{plan['ch4_avoided_kg_year']['base']:,.0f} kg CH₄/year"); e.caption(f"Range {plan['ch4_avoided_kg_year']['low']:,.0f}–{plan['ch4_avoided_kg_year']['high']:,.0f}")
    st.subheader("Why this is recommended"); st.markdown("\n".join(f"- {x}" for x in rec["reasons"][:3]))
    if rec["r5_note"]: st.info(rec["r5_note"])
    with st.expander("What could change this recommendation?"): st.write(rec["what_would_change"])
    with st.expander("Warnings and assumptions"):
        for w in rec["warnings"]: st.warning(w)
        st.caption("Planning guidance only; this is not a legal compliance decision or vendor quote.")
    st.subheader("Compare the options"); comparison(r)
    st.subheader("Implementation plan"); st.markdown("\n".join(f"{i}. {x}" for i, x in enumerate(plan["next_steps"], 1)))
    if plan["local_use_line"]: st.info(plan["local_use_line"])
    future = next(row for row in r["roadmap"]["rows"] if row["year"] == 2035)
    st.subheader("2035 outlook"); st.write(f"**2035 outlook:** {future['pathway']} is recommended at {future['food_waste_kg_week']:,.0f} kg/week.")
    with st.expander("View 2035 projection"):
        st.dataframe(pd.DataFrame(r["roadmap"]["rows"]), hide_index=True, use_container_width=True)
    if r["waste_profile"]["tenants"]:
        with st.expander("View waste by tenant"): st.dataframe(pd.DataFrame(r["waste_profile"]["tenants"]), hide_index=True, use_container_width=True)
    evidence()
    if st.button("Edit inputs"): st.session_state.show_results = False; st.rerun()


def about_page():
    st.header("About Circular Organics Planner")
    st.write("A planning aid for NSW building and facility managers, built for Climate Hack-tion 2026: Build for 2035.")
    st.subheader("How it works")
    st.markdown("1. Profile your waste stream\n2. Compare Off-site FOGO, Hybrid, and On-site\n3. Get a recommended implementation plan")
    with st.expander("Methodology & evidence"):
        st.write("The planner checks likely NSW mandate timing, sizes collections, compares three pathways, and applies the same engine rules through 2035.")
        st.caption("Detailed assumptions, confidence ranges, and source links are available below.")
    evidence()
    st.caption("Guidance only — confirm mandate duties with NSW EPA or your council, and obtain site approvals before purchasing equipment.")


init_state()
page = st.sidebar.radio("Menu", ["Planner", "About"])
st.sidebar.caption("Circular Organics Planner · illustrative prototype")
if page == "About": about_page()
elif st.session_state.show_results and "result" in st.session_state: results_page(st.session_state.result)
else: input_page()
