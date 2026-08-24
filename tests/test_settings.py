from settings import as_bool


def test_as_bool_accepts_bools_and_strings():
    assert as_bool(True) is True
    assert as_bool(False) is False
    assert as_bool("true") is True
    assert as_bool("True") is True
    assert as_bool("false") is False
    assert as_bool("") is False
    assert as_bool(None) is False
    assert as_bool(None, default=True) is True
