"""Circular Organics Planner: reference engine.

Pure functions, no UI. Every number comes from assumptions.csv (no hard-coded values
except the pathway labels, collection schedules and fixed messages).
Use it directly (Streamlit: plan_building(inputs, cfg)) or behind one API endpoint
(POST /api/plan: input JSON in, output JSON out). See SPEC.md for the contract.
"""
import csv
import math
from pathlib import Path

PATHWAYS = ["offsite", "hybrid", "onsite"]
LABELS = {"offsite": "Off-site FOGO", "hybrid": "Hybrid", "onsite": "On-site"}
LEVEL = {"offsite": 0, "hybrid": 1, "onsite": 2}
TENANT_TYPES = ["cafe", "restaurant", "quick_service", "bakery", "grocery"]

# Qualitative comparison (team design doc).
QUALITATIVE = {
    "offsite": {"space": "Low", "cost": "Low", "effort": "Low"},
    "hybrid": {"space": "Medium", "cost": "Medium", "effort": "Medium"},
    "onsite": {"space": "High", "cost": "High", "effort": "High"},
}

# Collection schedules: (collections per week, days, longest gap in days).
SCHEDULES = [
    (1, ["Mon"], 7),
    (2, ["Mon", "Thu"], 4),
    (3, ["Mon", "Wed", "Fri"], 3),
    (4, ["Mon", "Wed", "Fri", "Sun"], 2),
    (7, ["Daily"], 1),
]

ROADMAP_YEARS = [2026, 2028, 2030, 2035]
ROADMAP_ACTIONS = {
    2026: "Confirm the site scope, start separation in covered food-preparation areas, "
          "run a weighed audit and confirm a receiving facility.",
    2028: "Review measured capture, costs and collection reliability before choosing a larger system.",
    2030: "Recheck the expanded mandate and the end of the dining-area exemption (1 July 2030).",
    2035: "Review the on-site pre-processing exemption (expires 1 July 2035) and refresh emission factors.",
}

MANDATE_NOTES = [
    "In a shared waste service, the shared service decides when the mandate applies, and whoever "
    "holds the waste contract (often centre management) coordinates tenants and arranges collection.",
    "Check exemptions: front-of-house dining areas are exempt until 1 July 2030 (kitchens are still "
    "covered), and some regional and institutional exemptions apply.",
    "Guidance only. Confirm with NSW EPA or your council.",
]

PROCESSING_WARNING = ("Check approvals for the exact device. If you use the NSW on-site pre-processing "
                      "exemption, its conditions include sending the processed output to off-site resource "
                      "recovery (NSW EPA FOGO exemptions, S15 and S22). Our climate numbers assume the output "
                      "is recovered. Dehydrated food waste is not compost.")
ONSITE_WARNING = ("Regulatory and safety check required (approvals, ventilation, fire safety, trade waste) "
                  "before buying equipment.")


# ---------------------------------------------------------------- config
def load_config(path=None):
    path = Path(path) if path else Path(__file__).with_name("assumptions.csv")
    cfg = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cfg[row["key"]] = {
                "min": float(row["min"]), "base": float(row["base"]), "max": float(row["max"]),
                "unit": row["unit"], "item": row["item"], "source_id": row["source_id"],
                "source_url": row["source_url"], "confidence": row["confidence"],
            }
    return cfg


def v(cfg, key, which="base"):
    return cfg[key][which]


# ---------------------------------------------------------------- O1 waste profile
def waste_profile(inp, cfg):
    """W = entered total, or the sum of tenant estimates (measured kg overrides the type default)."""
    total = inp.get("total_food_waste_kg_week")
    if total not in (None, ""):
        return {"total_kg_week": float(total), "source": "entered", "tenants": []}
    rows, total = [], 0.0
    for t in inp.get("tenants", []):
        count = int(t.get("count", 1))
        if t.get("kg_week") not in (None, ""):
            kg_each, estimated = float(t["kg_week"]), False
        else:
            if t["type"] not in TENANT_TYPES:
                raise ValueError(f"Unknown tenant type: {t['type']}")
            size = t.get("size", "medium")
            factor = 1.0 if size == "medium" else v(cfg, f"size_factor_{size}")
            kg_each, estimated = v(cfg, f"waste_{t['type']}_kg_week") * factor, True
        kg = kg_each * count
        total += kg
        rows.append({"name": t.get("name", t.get("type", "tenant")), "type": t.get("type"),
                     "size": t.get("size", "medium"), "count": count,
                     "kg_week": round(kg, 1), "estimated": estimated})
    return {"total_kg_week": round(total, 1), "source": "estimated", "tenants": rows}


# ---------------------------------------------------------------- O9 mandate check (C0)
def mandate_check(bins, cfg, growth_factor=1.0):
    """bins = [{"size_l", "count", "collections_per_week"}] for GENERAL waste only."""
    if not bins:
        return {"capacity_l_week": None, "branch": None, "status_code": "unknown", "start_year": None,
                "status_text": "Enter your general waste bins to check the NSW mandate.",
                "notes": MANDATE_NOTES}
    capacity = sum(b["size_l"] * b["count"] * b["collections_per_week"] for b in bins) * growth_factor
    all_240 = all(b["size_l"] == 240 for b in bins)
    single_660 = any(b["size_l"] >= v(cfg, "mandate_2030_single_bin_l") for b in bins)
    t2026 = v(cfg, "mandate_2026_l_week") if all_240 else v(cfg, "mandate_2026_other_l_week")
    t2028 = v(cfg, "mandate_2028_l_week") if all_240 else v(cfg, "mandate_2028_other_l_week")
    t2030 = v(cfg, "mandate_2030_l_week")
    if capacity >= t2026:
        code, start, threshold = "covered_2026", 2026, t2026
        text = "Likely covered now (since 1 July 2026)"
    elif capacity >= t2028:
        code, start, threshold = "from_2028", 2028, t2028
        text = "Likely covered from 1 July 2028"
    elif capacity >= t2030 or single_660:
        code, start, threshold = "from_2030", 2030, t2030
        text = "Likely covered from 1 July 2030"
    else:
        code, start, threshold = "below", None, t2030
        text = "Below current thresholds (voluntary for now)"
    return {"capacity_l_week": round(capacity, 1), "branch": "240L" if all_240 else "other",
            "status_code": code, "start_year": start, "threshold_l_week": threshold,
            "status_text": text, "notes": MANDATE_NOTES}


def mandate_status_in_year(m, year):
    if m["start_year"] is None:
        return "Below thresholds" if m["status_code"] == "below" else "Unknown"
    if m["start_year"] <= year:
        return f"Covered (since 1 July {m['start_year']})"
    return f"From 1 July {m['start_year']}"


# ---------------------------------------------------------------- space and budget
def space_band(space_m2, cfg):
    if space_m2 < v(cfg, "space_moderate_min_m2"):
        return "Limited"
    if space_m2 < v(cfg, "space_ample_min_m2"):
        return "Moderate"
    return "Ample"


def budget_bands(cfg):
    """Labels for the budget select, from the equipment budget rows."""
    small_min, large_min = v(cfg, "equipment_small_aud", "min"), v(cfg, "equipment_large_aud", "min")
    return {"low": f"Under ${small_min:,.0f} (no equipment)",
            "medium": f"${small_min:,.0f} to ${large_min:,.0f} (small unit)",
            "high": f"${large_min:,.0f} or more (larger system)"}


# ---------------------------------------------------------------- O4 plan
def make_plan(W, pathway, room_m2, cfg):
    captured = W * v(cfg, "capture_rate")
    share = {"offsite": 0.0, "hybrid": v(cfg, "hybrid_onsite_share"),
             "onsite": v(cfg, "onsite_onsite_share")}[pathway]
    onsite_in = captured * share
    offsite_in = captured - onsite_in
    bin_l = v(cfg, "organics_bin_size_l")
    bin_mass = min(bin_l * v(cfg, "food_density_kg_per_l") * v(cfg, "bin_fill_fraction"),
                   v(cfg, "included_service_weight_kg"), v(cfg, "bin_filling_limit_kg"))
    max_gap = v(cfg, "max_days_between_collections")
    allowed = [s for s in SCHEDULES if s[2] <= max_gap]
    footprint = v(cfg, "bin_footprint_m2_240l")
    room_ok = True
    if offsite_in <= 0:
        freq, days, gap, bins = 0, [], None, 0
    else:
        for freq, days, gap in allowed:
            bins = math.ceil(offsite_in * gap / 7 / bin_mass)
            if bins * footprint <= room_m2:
                break
        else:
            room_ok = False  # even daily collection needs more floor space than the waste room has
    lifts = bins * freq
    price_key = {0: None, 1: "price_lift_1x_aud", 2: "price_lift_2x_aud", 3: "price_lift_3x_aud"}.get(
        freq, "price_lift_4plus_aud")
    cost = lifts * v(cfg, price_key) if price_key else 0.0
    return {"captured_kg_week": round(captured, 1), "offsite_kg_week": round(offsite_in, 1),
            "onsite_kg_week": round(onsite_in, 1), "uncaptured_kg_week": round(W - captured, 1),
            "bins": bins, "bin_size_l": int(bin_l), "bin_mass_kg": round(bin_mass, 3),
            "collections_per_week": freq, "collection_days": days, "lifts_per_week": lifts,
            "bins_floor_m2": round(bins * footprint, 2), "room_ok": room_ok,
            "collection_cost_aud_week": round(cost, 2)}


# ---------------------------------------------------------------- O5 impact
def impact(W, pathway, cfg):
    share = {"offsite": 0.0, "hybrid": v(cfg, "hybrid_onsite_share"),
             "onsite": v(cfg, "onsite_onsite_share")}[pathway]

    def calc(cap, ef_l, ef_off, ef_on, ch4):
        captured_t = W * cap / 1000
        on_t, off_t = captured_t * share, captured_t * (1 - share)
        net_t_week = captured_t * ef_l - off_t * ef_off - on_t * ef_on   # may be negative
        return net_t_week * 52, captured_t * ch4 * 52                    # t CO2e/yr, kg CH4/yr

    lo = calc(v(cfg, "capture_rate", "min"), v(cfg, "ef_landfill_t_per_t", "min"),
              v(cfg, "ef_offsite_processing_t_per_t", "max"), v(cfg, "ef_onsite_processing_t_per_t", "max"),
              v(cfg, "ch4_landfill_kg_per_t", "min"))
    base = calc(v(cfg, "capture_rate"), v(cfg, "ef_landfill_t_per_t"),
                v(cfg, "ef_offsite_processing_t_per_t"), v(cfg, "ef_onsite_processing_t_per_t"),
                v(cfg, "ch4_landfill_kg_per_t"))
    hi = calc(v(cfg, "capture_rate", "max"), v(cfg, "ef_landfill_t_per_t", "max"),
              v(cfg, "ef_offsite_processing_t_per_t", "min"), v(cfg, "ef_onsite_processing_t_per_t", "min"),
              v(cfg, "ch4_landfill_kg_per_t", "max"))
    captured = W * v(cfg, "capture_rate")
    return {"diverted_kg_week": round(captured, 1), "diverted_kg_year": round(captured * 52, 0),
            "net_ghg_t_year": {"low": round(lo[0], 2), "base": round(base[0], 2), "high": round(hi[0], 2)},
            "ch4_avoided_kg_year": {"low": round(lo[1], 0), "base": round(base[1], 0), "high": round(hi[1], 0)}}


# ---------------------------------------------------------------- O3 rules R0 to R5
def _unmet(W, space_m2, local_use, budget, cfg, target):
    T1, T2 = v(cfg, "t1_hybrid_kg_week"), v(cfg, "t2_onsite_kg_week")
    mod, amp = v(cfg, "space_moderate_min_m2"), v(cfg, "space_ample_min_m2")
    out = []
    if target == "hybrid":
        if W < T1:
            out.append(f"weekly food waste reaches {T1:,.0f} kg (now {W:,.0f} kg)")
        if space_m2 < mod:
            out.append(f"on-site space is at least {mod:g} m² (now {space_m2:g} m²)")
        if not local_use:
            out.append("a local use for processed material is secured")
        if budget not in ("medium", "high"):
            out.append("the equipment budget covers a small unit (Medium)")
    elif target == "onsite":
        if W < T2:
            out.append(f"weekly food waste reaches {T2:,.0f} kg (now {W:,.0f} kg)")
        if space_m2 < amp:
            out.append(f"on-site space is at least {amp:g} m² (now {space_m2:g} m²)")
        if budget != "high":
            out.append("the equipment budget covers a larger system (High)")
        if not local_use:
            out.append("a local use for processed material is secured")
    return out


def _join(items):
    """'a', 'a and b', 'a, b and c'."""
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def recommend(W, space_m2, local_use, budget, cfg, plans=None):
    T1, T2 = v(cfg, "t1_hybrid_kg_week"), v(cfg, "t2_onsite_kg_week")
    band = space_band(space_m2, cfg)
    fired, reasons, warnings, rejected = ["R0"], [], [], {}
    candidates = {"offsite"}
    if band == "Limited":
        fired.append("R1")
        msg = f"Not enough on-site space ({space_m2:g} m²; needs at least {v(cfg, 'space_moderate_min_m2'):g} m²)"
        rejected = {"hybrid": [msg], "onsite": [msg]}
    else:
        if W >= T1 and local_use and budget in ("medium", "high"):
            fired.append("R2")
            candidates.add("hybrid")
        if W >= T2 and band == "Ample" and budget == "high":
            fired.append("R3")
            candidates.add("onsite")
    choice = max(candidates, key=lambda p: LEVEL[p])
    r4 = choice == "onsite" and not local_use
    if r4:
        fired.append("R4")
        choice = "offsite"
        rejected["onsite"] = ["No local use for processed material"]

    if choice == "offsite":
        if band == "Limited":
            reasons.append(f"There is not enough space for on-site processing ({space_m2:g} m² available).")
        elif W < T1:
            reasons.append(f"Weekly food waste ({W:,.0f} kg) is below the Hybrid threshold ({T1:,.0f} kg).")
        if not local_use and band != "Limited":
            reasons.append("There is no local use for processed material yet.")
        elif budget == "low" and band != "Limited" and W >= T1:
            reasons.append("The equipment budget does not cover an on-site unit yet.")
        reasons.append("Off-site collection is the simplest option and meets the separation requirement at any size.")
        if r4:
            change = ("Secure a use for processed material (for example landscaping, a rooftop garden or a "
                      "processor contract) to unlock Hybrid or On-site.")
        else:
            unmet = _unmet(W, space_m2, local_use, budget, cfg, "hybrid")
            change = "Hybrid becomes the recommendation when " + _join(unmet) + "."
    elif choice == "hybrid":
        reasons.append(f"Weekly food waste ({W:,.0f} kg) is above the Hybrid threshold ({T1:,.0f} kg).")
        reasons.append(f"There is {band.lower()} on-site space ({space_m2:g} m²), a local use for processed "
                       "material and a budget for a small unit.")
        if plans:
            reasons.append(f"Processing part of it on site cuts off-site bin lifts from "
                           f"{plans['offsite']['lifts_per_week']} to {plans['hybrid']['lifts_per_week']} per week.")
        unmet = _unmet(W, space_m2, local_use, budget, cfg, "onsite")
        change = "On-site becomes a candidate when " + _join(unmet) + "."
        warnings.append(PROCESSING_WARNING)
    else:
        reasons.append(f"Weekly food waste ({W:,.0f} kg) is above the On-site threshold ({T2:,.0f} kg).")
        reasons.append(f"There is ample space ({space_m2:g} m²), a budget for a larger system and a local use "
                       "for processed material.")
        change = "This is the highest pathway. Check approvals and safety before buying equipment."
        warnings += [ONSITE_WARNING, PROCESSING_WARNING]

    r5_note = None
    if (plans and choice == "offsite" and band != "Limited"
            and plans["offsite"]["collections_per_week"] >= v(cfg, "r5_high_collections_per_week")
            and plans["hybrid"]["collections_per_week"] < plans["offsite"]["collections_per_week"]):
        fired.append("R5")
        unmet = _unmet(W, space_m2, local_use, budget, cfg, "hybrid")
        r5_note = (f"Collections are frequent ({plans['offsite']['collections_per_week']} per week). Hybrid could cut "
                   f"this to about {plans['hybrid']['collections_per_week']} per week once " + _join(unmet) + ".")

    return {"pathway": choice, "label": LABELS[choice], "space_band": band, "rules_fired": fired,
            "reasons": reasons[:3], "rejected": rejected, "warnings": warnings,
            "what_would_change": change, "r5_note": r5_note}


def next_steps(pathway, plan):
    days = " · ".join(plan["collection_days"])
    if pathway == "offsite":
        return [f"Request quotes from at least two FOGO collection providers for {plan['bins']} × "
                f"{plan['bin_size_l']} L bins, collected {days}.",
                "Brief tenants on what goes in the food bin and place bins in each kitchen.",
                "Weigh food waste for the first month, then revisit this plan."]
    if pathway == "hybrid":
        return [f"Get quotes for a small on-site unit sized to about {plan['onsite_kg_week'] / 7:,.0f} kg/day "
                "and check approvals.",
                f"Request FOGO collection for the remaining {plan['offsite_kg_week']:,.0f} kg/week "
                f"({plan['bins']} × {plan['bin_size_l']} L, {days}).",
                "Agree where the processed output will be used, then weigh volumes for a month."]
    return ["Commission a site design and regulatory check (approvals, ventilation, fire safety, trade waste).",
            f"Get quotes for a larger system sized to about {plan['onsite_kg_week'] / 7:,.0f} kg/day plus peak days.",
            f"Keep a FOGO service for the residual {plan['offsite_kg_week']:,.0f} kg/week and secure an outlet "
            "for processed output."]


def equipment_budget(pathway, cfg):
    if pathway == "offsite":
        return None
    key = "equipment_small_aud" if pathway == "hybrid" else "equipment_large_aud"
    return {"min": v(cfg, key, "min"), "max": v(cfg, key, "max"),
            "operating_aud_week": {"min": v(cfg, "onsite_operating_aud_week", "min"),
                                   "max": v(cfg, "onsite_operating_aud_week", "max")},
            "note": "Indicative budget, not a quote."}


# ---------------------------------------------------------------- O6 roadmap
def roadmap(inp, W, cfg):
    g = float(inp.get("annual_change_pct") or 0) / 100
    rows, cum = [], {"low": 0.0, "base": 0.0, "high": 0.0}
    for year in range(2026, 2036):
        f = (1 + g) ** (year - 2026)
        Wy = W * f
        m = mandate_check(inp.get("general_waste_bins", []), cfg, growth_factor=f)
        plans = {p: make_plan(Wy, p, float(inp["waste_room_area_m2"]), cfg) for p in PATHWAYS}
        rec = recommend(Wy, float(inp["onsite_space_m2"]), bool(inp["local_use"]),
                        inp.get("budget_level", "low"), cfg, plans)
        imp = impact(Wy, rec["pathway"], cfg)
        for k in cum:
            cum[k] += imp["net_ghg_t_year"][k]
        if year in ROADMAP_YEARS:
            rows.append({"year": year, "food_waste_kg_week": round(Wy, 0),
                         "mandate": mandate_status_in_year(m, year),
                         "pathway": rec["label"], "next_step": rec["what_would_change"],
                         "action": ROADMAP_ACTIONS[year]})
    return {"rows": rows, "annual_change_pct": g * 100,
            "cumulative_net_ghg_t_2026_2035": {k: round(x, 1) for k, x in cum.items()},
            "note": "Indicative: full years 2026 to 2035, inputs other than volume kept constant."}


# ---------------------------------------------------------------- whole result
def plan_building(inp, cfg):
    profile = waste_profile(inp, cfg)
    W = profile["total_kg_week"]
    room, space = float(inp["waste_room_area_m2"]), float(inp["onsite_space_m2"])
    local_use, budget = bool(inp["local_use"]), inp.get("budget_level", "low")
    plans = {p: make_plan(W, p, room, cfg) for p in PATHWAYS}
    impacts = {p: impact(W, p, cfg) for p in PATHWAYS}
    rec = recommend(W, space, local_use, budget, cfg, plans)
    comparison = {p: {"label": LABELS[p], **plans[p], **impacts[p], **QUALITATIVE[p],
                      "equipment_budget": equipment_budget(p, cfg)} for p in PATHWAYS}
    chosen = rec["pathway"]
    current = int(inp.get("current_collections_per_week") or 0)
    return {
        "building_name": inp.get("building_name", ""),
        "waste_profile": profile,
        "mandate": mandate_check(inp.get("general_waste_bins", []), cfg),
        "recommendation": rec,
        "comparison": comparison,
        "plan": {**comparison[chosen], "pathway": chosen,
                 "collections_change": comparison[chosen]["collections_per_week"] - current,
                 "next_steps": next_steps(chosen, plans[chosen]),
                 "local_use_line": ("Processed material can be used on site, for example in a rooftop garden."
                                    if local_use and chosen != "offsite" else None)},
        "roadmap": roadmap(inp, W, cfg),
        "budget_labels": budget_bands(cfg),
    }


if __name__ == "__main__":
    import json, sys
    cfg = load_config()
    data = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else None
    print(json.dumps(plan_building(data, cfg), indent=2))
