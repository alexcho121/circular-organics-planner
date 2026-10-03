"""The published demo cases must keep their validated numeric outputs."""
import json
from pathlib import Path

import pytest

from app.engine import load_config, plan_building


DATA = Path(__file__).resolve().parent.parent / "data"
EXAMPLES = json.loads((DATA / "examples.json").read_text(encoding="utf-8"))
EXPECTED = json.loads((DATA / "example_outputs.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", EXAMPLES)
def test_demo_output_matches_validated_snapshot(name):
    assert plan_building(EXAMPLES[name], load_config()) == EXPECTED[name]
