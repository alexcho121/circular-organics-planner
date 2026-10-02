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
    pass


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