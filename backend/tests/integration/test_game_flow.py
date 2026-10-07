import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from app.bkt.manager import BKTManager


def test_game_flow_bkt_update_smoke():
    mastery_by_skill = {
        "SOURCE": 0.30,
        "EVIDENCE": 0.40,
        "CONTEXT": 0.25,
        "VISUAL": 0.35,
    }

    for skill_code, mastery in mastery_by_skill.items():
        updated = BKTManager.update_skill(skill_code, mastery, correct=True)
        assert 0.0 <= updated <= 1.0
        assert updated >= mastery

    assert set(mastery_by_skill.keys()) == set(BKTManager.VALID_SKILLS)
