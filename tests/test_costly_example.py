"""Example costly test to demonstrate tiered testing system."""

import pytest


def test_normal_test() -> None:
    """A normal test that runs by default."""
    assert True


@pytest.mark.costly
def test_costly_operation() -> None:
    """A costly test that only runs when explicitly requested."""
    # This would normally be a slow operation like:
    # - Network calls to external APIs
    # - Large data processing
    # - Integration tests with real services
    assert True
