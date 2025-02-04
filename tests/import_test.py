import pytest


@pytest.mark.order(1)
def test_import():
    import simforge  # noqa: F401
