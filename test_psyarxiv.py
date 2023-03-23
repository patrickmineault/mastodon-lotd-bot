import pytest
import get_toots

@pytest.mark.slow
def test_psyarxiv():
    """Take a while"""
    url = "https://psyarxiv.com/u56p2/"
    data = get_toots.get_url_via_selenium(url)
    assert "<title>" in data
    assert "Elemental psychopathology" in data