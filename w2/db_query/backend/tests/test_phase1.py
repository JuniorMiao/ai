"""Smoke import — Phase 1 scaffold."""

def test_package_importable():
    import db_query

    assert hasattr(db_query, "main")
