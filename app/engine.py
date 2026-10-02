import json
import math
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

#bin 하나가 실제로 몇 kg 담을 수 있는지 계산
#↓
#수거 1회 사이에 발생하는 음식물 kg 계산
#↓
#필요한 bin 개수 계산
def calculate_bin_count(
    weekly_waste_kg,
    collections_per_week,
    bin_size_l,
    density_kg_per_l,
    fill_rate
):
    capacity_per_bin_kg = (
        bin_size_l
        * density_kg_per_l
        * fill_rate
    )

    waste_per_collection_kg = (
        weekly_waste_kg
        / collections_per_week
    )

    return math.ceil(
        waste_per_collection_kg
        / capacity_per_bin_kg
    )


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

# input값이 이상하거나 없을경우 계산전에 막음
def validate_input(input_data):
    required_fields = [
        "weeklyOrganicWasteKg",
        "availableSpaceM2",
        "collectionsPerWeek"
    ]

    for field in required_fields:
        if field not in input_data:
            raise ValueError(
                f"Missing required field: {field}"
            )

    if input_data["weeklyOrganicWasteKg"] < 0:
        raise ValueError(
            "Weekly organic waste cannot be negative"
        )

    if input_data["availableSpaceM2"] < 0:
        raise ValueError(
            "Available space cannot be negative"
        )

    if input_data["collectionsPerWeek"] <= 0:
        raise ValueError(
            "Collections per week must be greater than zero"
        )

