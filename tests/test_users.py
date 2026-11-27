from belfort.core.users import LOCAL_USER, current_user_id


def test_local_user_until_accounts():
    assert current_user_id() == LOCAL_USER == "local"
