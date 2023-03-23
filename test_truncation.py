from get_toots import truncate_paragraph

def test_truncate_text():
    sentence = "this is bad text"
    assert truncate_paragraph(sentence, 3) == "this is bad..."

    sentence = "this <is></is> bad text"
    assert truncate_paragraph(sentence, 3) == "this <is></is>..."