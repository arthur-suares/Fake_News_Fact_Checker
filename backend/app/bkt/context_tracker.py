"""
CONTEXT skill tracker.

Tracks user's ability to perceive omitted, distorted, or incompatible context.
"""

from app.bkt.base import SkillTracker
from app.bkt.engine import BKTEngine


class ContextTracker(SkillTracker):
    """Tracker for CONTEXT skill: perceiving context issues."""

    # CONTEXT-specific BKT parameters
    P_GUESS = 0.20      # Probability of guessing correctly about context
    P_SLIP = 0.05       # Probability of slipping
    P_TRANSITION = 0.10 # Probability of learning from one attempt

    def __init__(self):
        """Initialize the CONTEXT tracker with appropriate parameters."""
        self.engine = BKTEngine(
            p_guess=self.P_GUESS,
            p_slip=self.P_SLIP,
            p_transition=self.P_TRANSITION,
        )

    def update(self, mastery: float, correct: bool) -> float:
        """
        Update mastery probability for CONTEXT skill.

        Args:
            mastery: Current mastery probability (0 to 1)
            correct: Whether the user correctly identified context issues

        Returns:
            Updated mastery probability (0 to 1)
        """
        return self.engine.update(mastery, correct)

    def get_parameters(self) -> dict:
        """Return CONTEXT-specific BKT parameters."""
        return self.engine.get_parameters()
