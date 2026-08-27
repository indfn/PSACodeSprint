"""Root conftest — delegates to app/tests/conftest.py.

Phase 4 fix: root conftest was a placeholder with no fixtures, causing duplicate
fixture discovery and import confusion. Now explicitly documents that shared
fixtures live in app/tests/conftest.py and ensures clean import path.
No duplicate fixtures are defined here.
"""
