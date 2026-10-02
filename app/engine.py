import json
from pathlib import Path


def load_assumptions():
    file_path = (
        Path(__file__).resolve().parent.parent
        / "data"
        / "assumptions.json"
    )

    with open(file_path, "r") as file:
        return json.load(file)

def build_waste_profile(input_data, assumptions):
    return {
        "buildingType": input_data.get("buildingType"),
        "tenantCount": input_data.get("tenantCount"),
        "weeklyOrganicWasteKg": input_data.get(
            "weeklyOrganicWasteKg"
        ),
        "availableSpaceM2": input_data.get(
            "availableSpaceM2"
        ),
        "collectionsPerWeek": input_data.get(
            "collectionsPerWeek"
        ),
        "currentWasteCost": input_data.get(
            "currentWasteCost"
        ),
        "onsiteReuseAvailable": input_data.get(
            "onsiteReuseAvailable"
        )
    }


def calculate_offsite(profile, assumptions, rules):
    pass


def calculate_hybrid(profile, assumptions, rules):
    pass


def calculate_onsite(profile, assumptions, rules):
    pass


def recommend_scenario(scenarios, rules):
    pass


def build_implementation_plan(
    recommendation,
    profile,
    assumptions
):
    pass


def run_engine(input_data):
    pass