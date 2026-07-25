# This file makes `models/` a Python package, and re-exports every
# model so the rest of the app can do `from models import User`
# instead of `from models.user import User`.
#
# When you add a new table later (e.g. notes.py, tags.py), import
# it here too — that's the ONLY thing you need to touch in this
# file when extending the schema.

from models.user import User

__all__ = ["User"]