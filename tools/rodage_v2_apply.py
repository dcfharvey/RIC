"""Disposable deterministic patch generator for Rodage V2 generic activity vocabulary."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"{path}: expected one match, found {text.count(old)}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


replace_once(
    "src/vivarium/seed.py",
    '''    ("socialize", 600, 3600, -4, -1, -2, -1, True),\n)\nSEED_ACTIVITY_ALLOWED = (\n''',
    '''    ("socialize", 600, 3600, -4, -1, -2, -1, True),\n    # Activités génériques nécessaires au scénario V2; aucune ne connaît un personnage.\n    ("bathe", 1200, 3600, -2, 1, 0, 12, False),\n    ("work", 2700, 14400, -6, -4, -5, -2, True),\n)\nSEED_ACTIVITY_ALLOWED = (\n''',
)
replace_once(
    "src/vivarium/seed.py",
    '''    ("socialize", None, "salon"),\n)\n''',
    '''    ("socialize", None, "salon"),\n    ("bathe", "salle_de_bain", None),\n    ("bathe", "piscine", None),\n    ("work", "lieu_travail", None),\n    # Le salon contient un divan : le sommeil y est physiquement possible.\n    ("sleep", "salon", None),\n)\n''',
)
replace_once(
    "src/vivarium/sleep_physiology.py",
    '''    "sport": "vigorous",\n}\n''',
    '''    "sport": "vigorous",\n    "bathe": "none",\n    "work": "light",\n}\n''',
)
replace_once(
    "src/vivarium/action_options.py",
    '''    "gaming", "photography", "sport", "girly_care", "watch_tv", "socialize",\n})\n''',
    '''    "gaming", "photography", "sport", "girly_care", "watch_tv", "socialize", "bathe",\n})\n''',
)
