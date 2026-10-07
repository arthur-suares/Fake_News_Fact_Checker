"""
BKT Manager - Maps skills to their trackers.

This module serves as a registry and factory for skill trackers.
It provides a unified interface for updating skill mastery across all four skills.
"""

from app.bkt.base import SkillTracker
from app.bkt.source_tracker import SourceTracker
from app.bkt.evidence_tracker import EvidenceTracker
from app.bkt.context_tracker import ContextTracker
from app.bkt.visual_tracker import VisualTracker


class BKTManager:
    """
    Manager for BKT trackers.

    Maps each skill code (SOURCE, EVIDENCE, CONTEXT, VISUAL) to its corresponding tracker.
    Provides a unified interface for updating mastery probabilities.
    """

    # Skill codes (must match Skill.code values in database)
    SKILL_SOURCE = "SOURCE"
    SKILL_EVIDENCE = "EVIDENCE"
    SKILL_CONTEXT = "CONTEXT"
    SKILL_VISUAL = "VISUAL"

    # Registry mapping skill code to tracker
    _TRACKERS = {
        SKILL_SOURCE: SourceTracker(),
        SKILL_EVIDENCE: EvidenceTracker(),
        SKILL_CONTEXT: ContextTracker(),
        SKILL_VISUAL: VisualTracker(),
    }

    # List of valid skill codes
    VALID_SKILLS = list(_TRACKERS.keys())

    @classmethod
    def update_skill(cls, skill_code: str, mastery: float, correct: bool) -> float:
        """
        Update mastery probability for a specific skill.

        Args:
            skill_code: Code of the skill (SOURCE, EVIDENCE, CONTEXT, or VISUAL)
            mastery: Current mastery probability (0 to 1)
            correct: Whether the user answered correctly

        Returns:
            Updated mastery probability (0 to 1)

        Raises:
            ValueError: If skill_code is invalid or mastery is out of range
        """
        if skill_code not in cls._TRACKERS:
            raise ValueError(
                f"Invalid skill code: {skill_code}. "
                f"Valid skills are: {', '.join(cls.VALID_SKILLS)}"
            )

        tracker = cls._TRACKERS[skill_code]
        return tracker.update(mastery, correct)

    @classmethod
    def get_tracker(cls, skill_code: str) -> SkillTracker:
        """
        Get the tracker for a specific skill.

        Args:
            skill_code: Code of the skill

        Returns:
            SkillTracker instance

        Raises:
            ValueError: If skill_code is invalid
        """
        if skill_code not in cls._TRACKERS:
            raise ValueError(
                f"Invalid skill code: {skill_code}. "
                f"Valid skills are: {', '.join(cls.VALID_SKILLS)}"
            )
        return cls._TRACKERS[skill_code]

    @classmethod
    def get_all_trackers(cls) -> dict[str, SkillTracker]:
        """
        Get all registered trackers.

        Returns:
            Dictionary mapping skill codes to SkillTracker instances
        """
        return cls._TRACKERS.copy()

    @classmethod
    def validate_skill_code(cls, skill_code: str) -> bool:
        """
        Check if a skill code is valid.

        Args:
            skill_code: Code to validate

        Returns:
            True if valid, False otherwise
        """
        return skill_code in cls._TRACKERS
