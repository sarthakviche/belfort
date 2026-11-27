"""Who is using Belfort right now.

Every per-user table has a `user_id` column and filters on this value. Until accounts land (T43),
everyone is the single local user. T43 replaces the body of `current_user_id` and nothing else
needs to change.
"""

LOCAL_USER = "local"


def current_user_id(request=None) -> str:
    """The id of the signed-in user for this request, or the local user.

    Belfort runs on the user's own computer, so the signed-in user is the same for every request (T43): the session
    kept by core/auth.py. Without accounts set up, or when signed out, everyone is the local user."""
    from . import auth

    u = auth.user()
    return u["id"] if u else LOCAL_USER
