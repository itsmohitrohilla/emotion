from __future__ import annotations
from ..schemas.emotions import EMOTIONS
from .ansi import RED, YELLOW, GREEN, CYAN, GRAY, ORANGE

try:
    from ..schemas.extended_emotions import EXTENDED_EMOTIONS
except ImportError:
    EXTENDED_EMOTIONS: dict = {}

ALL_EMOTIONS: dict = {**EMOTIONS, **EXTENDED_EMOTIONS}

RELATIONSHIP_COLORS: dict[str, str] = {
    "friendship":       GREEN,
    "anger":            RED,
    "jealousy":         YELLOW,
    "respect":          CYAN,
    "mock":             ORANGE,
    "pity":             GRAY,
    "confusion":        YELLOW,
    "class_respect":    CYAN,
    "rivalry":          RED,
    "dependency":       CYAN,
    "mentor":           GREEN,
    "sibling":          GRAY,
    "legacy_meets_new": ORANGE,
    "coworkers":        GRAY,
}
