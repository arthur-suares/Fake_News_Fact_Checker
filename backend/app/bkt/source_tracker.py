"""
SOURCE skill tracker.

Tracks user's ability to analyze information source/origin.
"""

from app.bkt.base import SkillTracker
from app.bkt.engine import BKTEngine


class SourceTracker(SkillTracker):
    """Tracker for SOURCE skill: analyzing information source/origin."""

    # SOURCE-specific BKT parameters
    P_GUESS = 0.20      # Probability of guessing correctly about source
    P_SLIP = 0.05       # Probability of slipping (knowing but answering wrong)
    P_TRANSITION = 0.10 # Probability of learning from one attempt

    def __init__(self):
        """Initialize the SOURCE tracker with appropriate parameters."""
        self.engine = BKTEngine(
            p_guess=self.P_GUESS,
            p_slip=self.P_SLIP,
            p_transition=self.P_TRANSITION,
        )

    def update(self, mastery: float, correct: bool) -> float:
        """
        Update mastery probability for SOURCE skill.

        Args:
            mastery: Current mastery probability (0 to 1)
            correct: Whether the user answered correctly about the source

        Returns:
            Updated mastery probability (0 to 1)
        """
        return self.engine.update(mastery, correct)

    def get_parameters(self) -> dict:
        """Return SOURCE-specific BKT parameters."""
        return self.engine.get_parameters()
