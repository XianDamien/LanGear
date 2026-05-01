"""Current-user dependency shim for the MVP single-user runtime."""


def get_current_user_id() -> int:
    """Return the current user id.

    The MVP runtime is still single-user. Business code should depend on this
    function instead of hard-coding `1`, so later auth integration only changes
    the dependency layer.
    """

    return 1
