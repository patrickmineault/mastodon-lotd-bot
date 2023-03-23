import get_toots

def test_doi_resolve():
    assert get_toots.resolve_doi("http://dx.doi.org/10.1016/j.cell.2023.02.022") == 'https://www.cell.com/cell/fulltext/S0092-8674(23)00000-0'
    assert get_toots.resolve_doi("http://dx.doi.org/10.1038/s41586-023-05813-2") == 'https://www.nature.com/articles/s41586-023-05813-2'