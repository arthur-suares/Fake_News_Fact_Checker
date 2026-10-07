"""
EVIDENCE skill tracker.

Tracks user's ability to evaluate supporting evidence.
"""

from app.bkt.base import SkillTracker
from app.bkt.engine import BKTEngine


class EvidenceTracker(SkillTracker):
    """Tracker for EVIDENCE skill: evaluating supporting evidence."""

    # EVIDENCE-specific BKT parameters
    P_GUESS = 0.20      # Probability of guessing correctly about evidence
    P_SLIP = 0.05       # Probability of slipping
    P_TRANSITION = 0.10 # Probability of learning from one attempt

    def __init__(self):
        """Initialize the EVIDENCE tracker with appropriate parameters."""
        self.engine = BKTEngine(
            p_guess=self.P_GUESS,
            p_slip=self.P_SLIP,
            p_transition=self.P_TRANSITION,
        )

    def update(self, mastery: float, correct: bool) -> float:
        """
        Update mastery probability for EVIDENCE skill.

        Args:
            mastery: Current mastery probability (0 to 1)
            correct: Whether the user correctly evaluated the evidence

        Returns:
            Updated mastery probability (0 to 1)
        """
        return self.engine.update(mastery, correct)

    def get_parameters(self) -> dict:
        """Return EVIDENCE-specific BKT parameters."""
        return self.engine.get_parameters()
