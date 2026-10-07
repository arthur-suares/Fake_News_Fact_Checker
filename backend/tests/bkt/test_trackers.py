"""
Unit tests for BKT Trackers and Manager.

Tests skill-specific trackers and the manager that coordinates them.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

import pytest
from app.bkt.manager import BKTManager
from app.bkt.source_tracker import SourceTracker
from app.bkt.evidence_tracker import EvidenceTracker
from app.bkt.context_tracker import ContextTracker
from app.bkt.visual_tracker import VisualTracker


class TestTrackers:
    """Tests for skill-specific trackers."""

    def test_source_tracker_interface(self):
        """Test that SourceTracker implements the correct interface."""
        tracker = SourceTracker()
        
        # Should have update method
        assert hasattr(tracker, "update")
        assert callable(tracker.update)
        
        # Should have get_parameters method
        assert hasattr(tracker, "get_parameters")
        assert callable(tracker.get_parameters)

    def test_source_tracker_update(self):
        """Test SourceTracker.update method."""
        tracker = SourceTracker()
        
        mastery = 0.30
        new_mastery = tracker.update(mastery, correct=True)
        
        assert new_mastery > mastery
        assert 0 <= new_mastery <= 1

    def test_source_tracker_parameters(self):
        """Test that SourceTracker has proper parameters."""
        tracker = SourceTracker()
        params = tracker.get_parameters()
        
        assert "p_guess" in params
        assert "p_slip" in params
        assert "p_transition" in params

    def test_evidence_tracker_update(self):
        """Test EvidenceTracker.update method."""
        tracker = EvidenceTracker()
        
        mastery = 0.30
        new_mastery = tracker.update(mastery, correct=True)
        
        assert new_mastery > mastery
        assert 0 <= new_mastery <= 1

    def test_context_tracker_update(self):
        """Test ContextTracker.update method."""
        tracker = ContextTracker()
        
        mastery = 0.30
        new_mastery = tracker.update(mastery, correct=True)
        
        assert new_mastery > mastery
        assert 0 <= new_mastery <= 1

    def test_visual_tracker_update(self):
        """Test VisualTracker.update method."""
        tracker = VisualTracker()
        
        mastery = 0.30
        new_mastery = tracker.update(mastery, correct=True)
        
        assert new_mastery > mastery
        assert 0 <= new_mastery <= 1

    def test_all_trackers_same_interface(self):
        """Test that all trackers have the same interface."""
        trackers = [
            SourceTracker(),
            EvidenceTracker(),
            ContextTracker(),
            VisualTracker(),
        ]
        
        for tracker in trackers:
            # All should have update method
            assert hasattr(tracker, "update")
            
            # All should have get_parameters method
            assert hasattr(tracker, "get_parameters")
            
            # Test that they work
            result = tracker.update(0.5, correct=True)
            assert 0 <= result <= 1
            
            params = tracker.get_parameters()
            assert isinstance(params, dict)


class TestBKTManager:
    """Tests for BKTManager."""

    def test_manager_valid_skills(self):
        """Test that manager knows about all four skills."""
        assert BKTManager.SKILL_SOURCE in BKTManager.VALID_SKILLS
        assert BKTManager.SKILL_EVIDENCE in BKTManager.VALID_SKILLS
        assert BKTManager.SKILL_CONTEXT in BKTManager.VALID_SKILLS
        assert BKTManager.SKILL_VISUAL in BKTManager.VALID_SKILLS
        
        assert len(BKTManager.VALID_SKILLS) == 4

    def test_manager_update_skill_source(self):
        """Test manager update for SOURCE skill."""
        mastery = 0.30
        new_mastery = BKTManager.update_skill(BKTManager.SKILL_SOURCE, mastery, correct=True)
        
        assert new_mastery > mastery
        assert 0 <= new_mastery <= 1

    def test_manager_update_skill_evidence(self):
        """Test manager update for EVIDENCE skill."""
        mastery = 0.30
        new_mastery = BKTManager.update_skill(BKTManager.SKILL_EVIDENCE, mastery, correct=True)
        
        assert new_mastery > mastery
        assert 0 <= new_mastery <= 1

    def test_manager_update_skill_context(self):
        """Test manager update for CONTEXT skill."""
        mastery = 0.30
        new_mastery = BKTManager.update_skill(BKTManager.SKILL_CONTEXT, mastery, correct=True)
        
        assert new_mastery > mastery
        assert 0 <= new_mastery <= 1

    def test_manager_update_skill_visual(self):
        """Test manager update for VISUAL skill."""
        mastery = 0.30
        new_mastery = BKTManager.update_skill(BKTManager.SKILL_VISUAL, mastery, correct=True)
        
        assert new_mastery > mastery
        assert 0 <= new_mastery <= 1

    def test_manager_invalid_skill(self):
        """Test that manager rejects invalid skill code."""
        with pytest.raises(ValueError):
            BKTManager.update_skill("INVALID_SKILL", 0.5, correct=True)

    def test_manager_get_tracker(self):
        """Test that manager returns correct tracker."""
        tracker = BKTManager.get_tracker(BKTManager.SKILL_SOURCE)
        assert tracker is not None
        assert callable(tracker.update)

    def test_manager_get_invalid_tracker(self):
        """Test that manager rejects invalid skill for get_tracker."""
        with pytest.raises(ValueError):
            BKTManager.get_tracker("INVALID_SKILL")

    def test_manager_get_all_trackers(self):
        """Test that manager returns all trackers."""
        trackers = BKTManager.get_all_trackers()
        
        assert len(trackers) == 4
        assert BKTManager.SKILL_SOURCE in trackers
        assert BKTManager.SKILL_EVIDENCE in trackers
        assert BKTManager.SKILL_CONTEXT in trackers
        assert BKTManager.SKILL_VISUAL in trackers

    def test_manager_validate_skill_code(self):
        """Test skill code validation."""
        assert BKTManager.validate_skill_code(BKTManager.SKILL_SOURCE)
        assert BKTManager.validate_skill_code(BKTManager.SKILL_EVIDENCE)
        assert BKTManager.validate_skill_code(BKTManager.SKILL_CONTEXT)
        assert BKTManager.validate_skill_code(BKTManager.SKILL_VISUAL)
        
        assert not BKTManager.validate_skill_code("INVALID")

    def test_manager_all_skills_return_valid_mastery(self):
        """Test that all skills return valid mastery updates."""
        for skill_code in BKTManager.VALID_SKILLS:
            result = BKTManager.update_skill(skill_code, 0.5, correct=True)
            assert 0 <= result <= 1
            
            result = BKTManager.update_skill(skill_code, 0.5, correct=False)
            assert 0 <= result <= 1

    def test_manager_sequence_updates(self):
        """Test a sequence of updates for different skills."""
        mastery_source = 0.30
        mastery_evidence = 0.40
        
        # Update different skills
        mastery_source = BKTManager.update_skill(
            BKTManager.SKILL_SOURCE, mastery_source, correct=True
        )
        mastery_evidence = BKTManager.update_skill(
            BKTManager.SKILL_EVIDENCE, mastery_evidence, correct=False
        )
        
        assert mastery_source > 0.30
        assert mastery_evidence < 0.40


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
