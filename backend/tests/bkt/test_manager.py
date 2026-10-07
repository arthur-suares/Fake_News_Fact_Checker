import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from app.bkt.manager import BKTManager


def test_bkt_manager_updates_mastery_for_each_skill():
    mastery = 0.30

    for skill_code in BKTManager.VALID_SKILLS:
        mastery = BKTManager.update_skill(skill_code, mastery, correct=True)
        assert 0.0 <= mastery <= 1.0

    assert mastery > 0.30


def test_bkt_manager_rejects_invalid_skill():
    try:
        BKTManager.update_skill("INVALID_SKILL", 0.5, correct=True)
        assert False, "Expected ValueError for invalid skill"
    except ValueError:
        pass
