"""
Shared FastAPI dependencies.
"""


def get_current_user_id() -> str:
    """
    Return the ID of the user making the request.

    TODO: Read the user from the JWT issued by /auth/login.
    Until then every request is attributed to the placeholder user, the same
    one used by the other game routes.
    """
    return "test-user"
