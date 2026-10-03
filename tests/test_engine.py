"""Acceptance tests for the Circular Organics Planner engine (run: pytest -q).

Each case states the input in plain words and the expected result. The same cases are listed
in test_cases.md for the team. Boundaries are inclusive: W = T1 counts as reaching T1.
"""
import pytest
from app.engine import load_config, plan_building, mandate_check, impact

CFG = load_config()


def building(**kw):
    base = {"total_food_waste_kg_week": 300, "current_collections_per_week": 0,
            "general_waste_bins": [{"size_l": 240, "count": 3, "collections_per_week": 2}],
            "waste_room_area_m2": 10, "onsite_space_m2": 0, "local_use": False,
            "budget_level": "low", "annual_change_pct": 0}
    base.update(kw)
    return base


CASES = [
    ("T01", "Small building, no on-site space",
     building(total_food_waste_kg_week=150, waste_room_area_m2=5),
     {"pathway": "offsite", "rules": ["R0", "R1"], "mandate": "from_2030"}),
    ("T02", "Large building but on-site space is Limited (R1 wins)",
     building(total_food_waste_kg_week=2000, onsite_space_m2=2, local_use=True, budget_level="high",
              waste_room_area_m2=20, general_waste_bins=[{"size_l": 660, "count": 6, "collections_per_week": 3}]),
     {"pathway": "offsite", "rules": ["R0", "R1"], "mandate": "covered_2026"}),
    ("T03", "Medium volume, Moderate space, local use, Medium budget",
     building(total_food_waste_kg_week=800, onsite_space_m2=8, local_use=True, budget_level="medium",
              general_waste_bins=[{"size_l": 240, "count": 10, "collections_per_week": 2}]),
     {"pathway": "hybrid", "rules": ["R0", "R2"], "mandate": "covered_2026"}),
    ("T04", "Large volume, Ample space, High budget",
     building(total_food_waste_kg_week=2000, onsite_space_m2=20, local_use=True, budget_level="high",
              waste_room_area_m2=20),
     {"pathway": "onsite", "rules": ["R0", "R2", "R3"], "warning": "Regulatory and safety check"}),
    ("T11", "Large volume, Ample space, but only a Medium budget",
     building(total_food_waste_kg_week=2000, onsite_space_m2=20, local_use=True, budget_level="medium",
              waste_room_area_m2=20),
     {"pathway": "hybrid", "rules": ["R0", "R2"], "change": "larger system (High)"}),
    ("T12", "Hybrid conditions met except budget (Low)",
     building(total_food_waste_kg_week=800, onsite_space_m2=8, local_use=True, budget_level="low"),
     {"pathway": "offsite", "rules": ["R0"], "change": "small unit (Medium)"}),
    ("T05", "On-site conditions met but no local use (R4)",
     building(total_food_waste_kg_week=2000, onsite_space_m2=20, local_use=False, budget_level="high",
              waste_room_area_m2=20),
     {"pathway": "offsite", "rules": ["R0", "R3", "R4"], "change": "Secure a use for processed material"}),
    ("T06", "Exactly at T1 (500 kg) with exactly 6 m2",
     building(total_food_waste_kg_week=500, onsite_space_m2=6, local_use=True, budget_level="medium"),
     {"pathway": "hybrid", "rules": ["R0", "R2"]}),
    ("T07", "R5 note: waste room too small, daily collection needed",
     building(total_food_waste_kg_week=1200, onsite_space_m2=8, local_use=False, waste_room_area_m2=2),
     {"pathway": "offsite", "rules": ["R0", "R5"], "collections": 7, "r5": "cut this to about 4 per week"}),
    ("T09", "Roadmap: 10% growth a year moves Off-site to Hybrid",
     building(total_food_waste_kg_week=400, onsite_space_m2=8, local_use=True, budget_level="medium",
              annual_change_pct=10),
     {"roadmap": ["Off-site FOGO", "Off-site FOGO", "Hybrid", "Hybrid"]}),
    ("T10", "Tenant estimate: measured kg overrides the type default",
     {**building(), "total_food_waste_kg_week": None,
      "tenants": [{"type": "cafe", "size": "medium", "count": 2},
                  {"type": "restaurant", "size": "large", "count": 1},
                  {"type": "bakery", "kg_week": 80, "count": 1}]},
     {"w": 680.0}),
]


@pytest.mark.parametrize("cid,desc,inp,exp", CASES, ids=[c[0] for c in CASES])
def test_case(cid, desc, inp, exp):
    r = plan_building(inp, CFG)
    rec = r["recommendation"]
    if "pathway" in exp:
        assert rec["pathway"] == exp["pathway"]
    if "rules" in exp:
        assert rec["rules_fired"] == exp["rules"]
    if "mandate" in exp:
        assert r["mandate"]["status_code"] == exp["mandate"]
    if "warning" in exp:
        assert any(exp["warning"] in w for w in rec["warnings"])
    if "change" in exp:
        assert exp["change"] in rec["what_would_change"]
    if "collections" in exp:
        assert r["plan"]["collections_per_week"] == exp["collections"]
    if "r5" in exp:
        assert exp["r5"] in rec["r5_note"]
    if "roadmap" in exp:
        assert [row["pathway"] for row in r["roadmap"]["rows"]] == exp["roadmap"]
    if "w" in exp:
        assert r["waste_profile"]["total_kg_week"] == exp["w"]


@pytest.mark.parametrize("bins,code", [
    ([{"size_l": 240, "count": 16, "collections_per_week": 1}], "covered_2026"),   # 3,840 L exactly
    ([{"size_l": 240, "count": 15, "collections_per_week": 1}], "from_2028"),      # 3,600 L
    ([{"size_l": 660, "count": 6, "collections_per_week": 1}], "covered_2026"),    # 3,960 L, other branch
    ([{"size_l": 660, "count": 1, "collections_per_week": 1}], "from_2030"),       # single 660 L bin
    ([{"size_l": 240, "count": 2, "collections_per_week": 1}], "below"),           # 480 L
], ids=["T08a-3840", "T08b-3600", "T08c-3960-other", "T08d-single-660", "T08e-480"])
def test_mandate_boundaries(bins, code):
    assert mandate_check(bins, CFG)["status_code"] == code


def test_research_cross_check():
    """Yeonsu's worked example at W = 600: Hybrid 0.432222, Off-site 0.534996 t CO2e/week."""
    assert impact(600, "hybrid", CFG)["net_ghg_t_year"]["base"] == pytest.approx(0.432222 * 52, abs=0.01)
    assert impact(600, "offsite", CFG)["net_ghg_t_year"]["base"] == pytest.approx(0.534996 * 52, abs=0.01)
