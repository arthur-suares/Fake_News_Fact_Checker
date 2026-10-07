"""
BKT (Bayesian Knowledge Tracing) Mathematical Engine.

Pure mathematical implementation of BKT. No dependencies on database, API, or frontend.

Formula:
    P(Ln+1) = P(Ln) * P(T) + (1 - P(Ln)) * P(T)
    
    If observation = correct:
        P(L | correct) = P(L) * (1 - P(S)) / [P(L) * (1 - P(S)) + (1 - P(L)) * P(G)]
    
    If observation = incorrect:
        P(L | incorrect) = P(L) * P(S) / [P(L) * P(S) + (1 - P(L)) * (1 - P(G))]

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
        for name, value in [
            ("p_guess", p_guess),
            ("p_slip", p_slip),
            ("p_transition", p_transition),
            ("p_init", p_init),
        ]:
            if not (0 <= value <= 1):
                raise ValueError(f"{name} must be between 0 and 1, got {value}")

        self.p_guess = p_guess
        self.p_slip = p_slip
        self.p_transition = p_transition
        self.p_init = p_init

    def update(self, mastery: float, correct: bool) -> float:
        """
        Update mastery probability based on observation (correct/incorrect answer).

        Args:
            mastery: Current mastery probability (0 to 1)
            correct: Whether the answer was correct

        Returns:
            Updated mastery probability, constrained to [0, 1]

        Raises:
            ValueError: If mastery is not in [0, 1]
        """
        if not (0 <= mastery <= 1):
            raise ValueError(f"mastery must be between 0 and 1, got {mastery}")

        # Step 1: Apply transition - probability of learning
        predicted = mastery * (1 - self.p_transition) + (1 - mastery) * self.p_transition

        # Step 2: Apply observation (correct/incorrect) using Bayes rule
        if correct:
            # User answered correctly
            # P(mastered | correct) = P(mastered) * P(correct | mastered) / P(correct)
            numerator = predicted * (1 - self.p_slip)
            denominator = predicted * (1 - self.p_slip) + (1 - predicted) * self.p_guess
        else:
            # User answered incorrectly
            # P(mastered | incorrect) = P(mastered) * P(incorrect | mastered) / P(incorrect)
            numerator = predicted * self.p_slip
            denominator = predicted * self.p_slip + (1 - predicted) * (1 - self.p_guess)

        # Avoid division by zero
        if denominator == 0:
            return predicted

        updated_mastery = numerator / denominator

        # Ensure result is within bounds
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
