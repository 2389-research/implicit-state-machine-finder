# ABOUTME: Per-account display and notification preferences.
# ABOUTME: Each preference is set on its own from the settings page.
from dataclasses import dataclass


@dataclass
class Prefs:
    dark_mode: bool = False
    compact_lists: bool = False
    email_digest: bool = True
    is_beta_tester: bool = False


def update(prefs, **changes):
    for key, value in changes.items():
        if not hasattr(prefs, key):
            raise KeyError(key)
        setattr(prefs, key, bool(value))
    return prefs
