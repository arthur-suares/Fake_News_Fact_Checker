"""
BKT (Bayesian Knowledge Tracing) Mathematical Engine.

Pure mathematical implementation of BKT. No dependencies on database, API, or frontend.

Formula:
    First update mastery from the observation using Bayes' rule:
        P(L | correct) = P(L) * (1 - P(S)) / [P(L) * (1 - P(S)) + (1 - P(L)) * P(G)]
        P(L | incorrect) = P(L) * P(S) / [P(L) * P(S) + (1 - P(L)) * (1 - P(G))]

    Then apply learning transition:
        P(L_next) = P(L | observation) + (1 - P(L | observation)) * P(T)

Where:
    P(L0) = Prior probability of mastery (initial state)
    P(T)  = Probability of transition (moving from not-mastered to mastered)
    P(G)  = Probability of guessing correctly despite not knowing
    P(S)  = Probability of slipping (knowing but answering incorrectly)
"""


class BKTEngine:
    """
    Core BKT engine for updating skill mastery probabilities.

    This class is stateless - it only performs mathematical calculations.
    It does not access the database or maintain any state between calls.
    """

    # Default BKT parameters
    DEFAULT_P_GUESS = 0.20      # Probability of guessing correctly
    DEFAULT_P_SLIP = 0.05       # Probability of slipping (knowing but answering wrong)
    DEFAULT_P_TRANSITION = 0.10 # Probability of learning from one attempt
    DEFAULT_P_INIT = 0.30       # Initial mastery probability

    def __init__(
        self,
        p_guess: float = DEFAULT_P_GUESS,
        p_slip: float = DEFAULT_P_SLIP,
        p_transition: float = DEFAULT_P_TRANSITION,
        p_init: float = DEFAULT_P_INIT,
    ):
        """
        Initialize the BKT engine with parameters.

        Args:
            p_guess: Probability of guessing correctly (0 to 1)
            p_slip: Probability of slipping (0 to 1)
            p_transition: Probability of learning (0 to 1)
            p_init: Initial mastery probability (0 to 1)

        Raises:
            ValueError: If any parameter is outside [0, 1]
        """
        self._validate_probabilities(
            p_guess=p_guess,
            p_slip=p_slip,
            p_transition=p_transition,
            p_init=p_init,
        )

        self.p_guess = p_guess
        self.p_slip = p_slip
        self.p_transition = p_transition
        self.p_init = p_init

    @staticmethod
    def _validate_probabilities(**values: float) -> None:
        """Raise ValueError if any named value is outside [0, 1]."""
        for name, value in values.items():
            if not (0 <= value <= 1):
                raise ValueError(f"{name} must be between 0 and 1, got {value}")

    def update(
        self,
        mastery: float,
        correct: bool,
        p_guess: float | None = None,
        p_slip: float | None = None,
        p_transition: float | None = None,
    ) -> float:
        """
        Update mastery probability based on observation (correct/incorrect answer).

        Args:
            mastery: Current mastery probability (0 to 1)
            correct: Whether the answer was correct
            p_guess: Overrides the engine's p_guess for this call
            p_slip: Overrides the engine's p_slip for this call
            p_transition: Overrides the engine's p_transition for this call

        Returns:
            Updated mastery probability, constrained to [0, 1]

        Raises:
            ValueError: If mastery or any parameter is not in [0, 1]
        """
        p_guess = self.p_guess if p_guess is None else p_guess
        p_slip = self.p_slip if p_slip is None else p_slip
        p_transition = self.p_transition if p_transition is None else p_transition

        self._validate_probabilities(
            mastery=mastery,
            p_guess=p_guess,
            p_slip=p_slip,
            p_transition=p_transition,
        )

        # Step 1: Apply the observation using Bayes' rule.
        if correct:
            # User answered correctly
            numerator = mastery * (1 - p_slip)
            denominator = numerator + (1 - mastery) * p_guess
        else:
            # User answered incorrectly
            numerator = mastery * p_slip
            denominator = numerator + (1 - mastery) * (1 - p_guess)

        if denominator == 0:
            posterior = mastery
        else:
            posterior = numerator / denominator

        # Step 2: Learning can move an unmastered learner to mastery, not reverse it.
        updated_mastery = posterior + (1 - posterior) * p_transition
        return max(0.0, min(1.0, updated_mastery))

    def get_parameters(self) -> dict:
        """
        Return current BKT parameters.

        Returns:
            Dictionary with keys: p_guess, p_slip, p_transition, p_init
        """
        return {
            "p_guess": self.p_guess,
            "p_slip": self.p_slip,
            "p_transition": self.p_transition,
            "p_init": self.p_init,
        }
