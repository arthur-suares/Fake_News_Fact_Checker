"""
Abstract base class for skill trackers.

All skill trackers (SOURCE, EVIDENCE, CONTEXT, VISUAL) must implement this interface.
This ensures compatibility and allows parallel development of different trackers.
"""

from abc import ABC, abstractmethod


class SkillTracker(ABC):
    """Abstract base class for tracking skill mastery using BKT."""

    @abstractmethod
    def update(self, mastery: float, correct: bool) -> float:
        """
        Update the mastery probability based on user's answer.

        Args:
            mastery: Current mastery probability (0 to 1)
            correct: Whether the user answered correctly

        Returns:
            Updated mastery probability (0 to 1)

        Raises:
            ValueError: If mastery is not between 0 and 1
        """
        pass

    @abstractmethod
    def get_parameters(self) -> dict:
        """
        Return the BKT parameters used by this tracker.

        Returns:
            Dictionary with keys: p_guess, p_slip, p_transition
        """
        pass
