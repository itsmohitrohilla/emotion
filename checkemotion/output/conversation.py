from __future__ import annotations

import os
import random
from typing import Optional

from ..utils.ansi import RESET, BOLD, DIM, CYAN
from ..utils.dialogue_data import EMOTION_VOICES, RELATIONSHIP_EXCHANGES, STAT_BANTER
from ..utils.emotion_lookup import ALL_EMOTIONS, RELATIONSHIP_COLORS

try:
    from ..core.registry import get_data as registry_get_data
except Exception:
    registry_get_data = None


def get_emotion_family(emotion: str) -> str:
    return ALL_EMOTIONS.get(emotion, {}).get("family", emotion)


def get_emotion_color(emotion: str) -> str:
    return ALL_EMOTIONS.get(emotion, {}).get("color", "")


def get_emotion_emoji(emotion: str) -> str:
    return ALL_EMOTIONS.get(emotion, {}).get("emoji", "🤖")


def pick_voice(emotion: str) -> str:
    family = get_emotion_family(emotion)
    phrases = EMOTION_VOICES.get(family, EMOTION_VOICES.get(emotion, [f"Running as {emotion}."]))
    return random.choice(phrases)


def generate_dialogue(
    func_a: str, stats_a: dict,
    func_b: str, stats_b: dict,
    emotion_a: str, emotion_b: str,
    relationship: Optional[str],
) -> tuple[str, str]:
    sa = {
        "calls":  stats_a.get("call_count", 0),
        "errors": stats_a.get("exception_count", 0),
        "ms":     stats_a.get("average_time_ms", 0.0),
    }
    sb = {
        "calls":  stats_b.get("call_count", 0),
        "errors": stats_b.get("exception_count", 0),
        "ms":     stats_b.get("average_time_ms", 0.0),
    }

    def format_banter_line(tmpl: str) -> str:
        pct_a = int(sa["errors"] / sa["calls"] * 100) if sa["calls"] else 0
        ok_a  = sa["calls"] - sa["errors"]
        return tmpl.format(
            a=func_a, b=func_b,
            calls_a=sa["calls"], errors_a=sa["errors"], ms_a=f"{sa['ms']:.1f}",
            calls_b=sb["calls"], errors_b=sb["errors"], ms_b=f"{sb['ms']:.1f}",
            pct_a=pct_a, ok_a=ok_a,
        )

    candidates = []
    for condition, templates in STAT_BANTER:
        try:
            if condition(sa, sb):
                candidates.extend(templates)
        except Exception:
            pass
    if candidates:
        raw_a, raw_b = random.choice(candidates)
        try:
            return format_banter_line(raw_a), format_banter_line(raw_b)
        except Exception:
            pass

    if relationship and relationship in RELATIONSHIP_EXCHANGES:
        init_phrases, resp_phrases = RELATIONSHIP_EXCHANGES[relationship]
        return random.choice(init_phrases), random.choice(resp_phrases)

    return pick_voice(emotion_a), pick_voice(emotion_b)


def display_conversation(
    func_a: str,
    emotion_a: str,
    func_b: str,
    emotion_b: str,
    relationship: str | None,
) -> None:
    try:
        width = min(os.get_terminal_size().columns, 100)
    except OSError:
        width = 90

    stats_a: dict = {}
    stats_b: dict = {}
    if registry_get_data is not None:
        try:
            stats_a = registry_get_data(func_a) or {}
            stats_b = registry_get_data(func_b) or {}
        except Exception:
            pass

    color_a = get_emotion_color(emotion_a)
    color_b = get_emotion_color(emotion_b)
    emoji_a = get_emotion_emoji(emotion_a)
    emoji_b = get_emotion_emoji(emotion_b)

    inner_w   = width - 4
    title     = " ⚡ FUNCTION DIALOGUE "
    title_pad = title.center(inner_w, "─")

    print(f"\n{DIM}╔{'═' * inner_w}╗{RESET}")
    print(f"{DIM}║{RESET}{BOLD}{title_pad}{RESET}{DIM}║{RESET}")
    print(f"{DIM}╠{'═' * inner_w}╣{RESET}")

    if relationship:
        rel_color = RELATIONSHIP_COLORS.get(relationship, CYAN)
        rel_line = (
            f"  {rel_color}{BOLD}{relationship.upper()}{RESET}"
            f"  ·  {color_a}{BOLD}{emoji_a} {func_a}{RESET} [{emotion_a}]"
            f"  ↔  {color_b}{BOLD}{emoji_b} {func_b}{RESET} [{emotion_b}]"
        )
        print(f"{DIM}║{RESET} {rel_line}")
        print(f"{DIM}╠{'─' * inner_w}╣{RESET}")

    label_a = f"{color_a}{BOLD}{emoji_a} {func_a}{RESET}"
    label_b = f"{color_b}{BOLD}{emoji_b} {func_b}{RESET}"

    line_a, line_b = generate_dialogue(
        func_a, stats_a, func_b, stats_b, emotion_a, emotion_b, relationship
    )
    print(f"{DIM}║{RESET}  {label_a}  {DIM}says:{RESET}  {line_a}")
    print(f"{DIM}║{RESET}  {label_b}  {DIM}says:{RESET}  {line_b}")

    print(f"{DIM}╚{'═' * inner_w}╝{RESET}\n")
