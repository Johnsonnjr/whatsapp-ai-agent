from router.relationship_router import resolve_relationship


def test_invalid_jid_returns_unknown():
    relationship, collection = resolve_relationship(None)
    assert relationship == "unknown"
    assert collection == "history_unknown"


def test_group_jid_returns_group():
    relationship, collection = resolve_relationship("123456789@g.us")
    assert relationship == "group"
    assert collection is None