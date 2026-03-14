from __future__ import annotations

import os

from ..schemas.emotions import EMOTIONS, RESET, BOLD, DIM
from ..utils.emotion_lookup import ALL_EMOTIONS

ansi_color = lambda n: f"\033[38;5;{n}m"  # noqa: E731

ITALIC    = "\033[3m"
UNDERLINE = "\033[4m"

GOLD   = ansi_color(220)
SILVER = ansi_color(250)
GRAY   = ansi_color(240)
DGRAY  = ansi_color(236)

VALENCE_COLORS: dict[str, str] = {
    "positive": ansi_color(82),
    "negative": ansi_color(196),
    "mixed":    ansi_color(214),
}

INTENSITY_BARS = ["░", "▒", "▓", "█", "█"]

REGISTRATION_BANNERS = [
    "▸ awakened",
    "◆ initialized",
    "✦ activated",
    "⬡ registered",
    "⚙ configured",
    "◈ calibrated",
    "❋ initialized",
    "⊕ engaged",
]

BANNER_INDEX = 0


def next_banner() -> str:
    global BANNER_INDEX
    banner = REGISTRATION_BANNERS[BANNER_INDEX % len(REGISTRATION_BANNERS)]
    BANNER_INDEX += 1
    return banner


def terminal_width() -> int:
    try:
        return min(os.get_terminal_size().columns, 110)
    except OSError:
        return 90


def get_emotion_info(emotion: str) -> dict:
    return ALL_EMOTIONS.get(emotion, ALL_EMOTIONS.get("content", {
        "emoji": "🤖", "color": ansi_color(245), "family": "unknown",
        "intensity": 1, "valence": "mixed",
    }))


def intensity_bar(intensity: int) -> str:
    filled  = min(intensity, 5)
    char    = INTENSITY_BARS[filled - 1]
    colors  = [ansi_color(240), ansi_color(246), ansi_color(214), ansi_color(208), ansi_color(196)]
    color   = colors[filled - 1]
    return f"{color}{''.join(char * filled)}{RESET}{GRAY}{'·' * (5 - filled)}{RESET}"


def valence_badge(valence: str) -> str:
    symbols = {"positive": "▲ +", "negative": "▼ −", "mixed": "◆ ±"}
    colors  = {"positive": ansi_color(82), "negative": ansi_color(196), "mixed": ansi_color(214)}
    sym = symbols.get(valence, "◆ ?")
    col = colors.get(valence, ansi_color(245))
    return f"{col}{sym}{RESET}"


def say(emotion: str, func_name: str, message: str) -> None:
    info      = get_emotion_info(emotion)
    color     = info.get("color", ansi_color(245))
    emoji     = info.get("emoji", "🤖")
    family    = info.get("family", "unknown")
    intensity = info.get("intensity", 1)
    valence   = info.get("valence", "mixed")

    ibar  = intensity_bar(intensity)
    vbadge = valence_badge(valence)

    tag      = f"{color}{BOLD}{emoji} {func_name}{RESET}"
    family_s = f"{DIM}[{family}·{emotion}]{RESET}"
    right    = f"{ibar}  {vbadge}"

    print(f"  {tag}  {family_s}  {right}")
    print(f"  {GRAY}{'╌' * 4}{RESET}  {SILVER}{message}{RESET}")


def say_registration(emotion: str, func_name: str, message: str) -> None:
    info   = get_emotion_info(emotion)
    color  = info.get("color", ansi_color(245))
    emoji  = info.get("emoji", "🤖")
    family = info.get("family", "unknown")

    desc = message if len(message) <= 60 else message[:57] + "…"

    print(
        f"  {color}{BOLD}{emoji}  {func_name}{RESET}"
        f"  {GRAY}▸{RESET}  {color}{emotion}{RESET}"
        f"  {DIM}[{family}]{RESET}"
        f"  {SILVER}{ITALIC}{desc}{RESET}"
    )


def running(func_name: str) -> None:
    print(f"  {DGRAY}┄┄ {func_name} running ┄┄{RESET}")


def separator() -> None:
    print()


def say_evolution(
    func_name: str,
    old_emotion: str,
    new_emotion: str,
) -> None:
    old_info  = get_emotion_info(old_emotion)
    new_info  = get_emotion_info(new_emotion)
    old_color = old_info.get("color", ansi_color(245))
    new_color = new_info.get("color", ansi_color(245))
    old_emoji = old_info.get("emoji", "🤖")
    new_emoji = new_info.get("emoji", "🤖")

    print(
        f"  {GOLD}⟳ DRIFT{RESET}  "
        f"{old_color}{old_emoji} {func_name}{RESET}"
        f"  {GRAY}──▶{RESET}  "
        f"{new_color}{BOLD}{new_emoji} {new_emotion}{RESET}"
        f"  {GRAY}(emotion evolved){RESET}"
    )


def print_metrics_row(
    func_name: str,
    emotion: str,
    *,
    exception_raised: bool,
    call_count: int,
    wall_ms: float,
    cpu_ms: float,
    mem_delta_kb: float,
    mem_peak_kb: float,
    cyclomatic_complexity: int,
    exception_count: int,
    conversation_partner: str | None = None,
    conversation_partner_emotion: str | None = None,
) -> None:
    info  = get_emotion_info(emotion)
    color = info.get("color", ansi_color(245))
    emoji = info.get("emoji", "🤖")

    err_color  = ansi_color(196) if exception_count > 0 else ansi_color(240)
    avg_color  = ansi_color(196) if wall_ms > 500 else (ansi_color(214) if wall_ms > 100 else ansi_color(82))
    status_sym = "💥" if exception_raised else "✓"

    conv_part = ""
    if conversation_partner and conversation_partner_emotion:
        p_info  = get_emotion_info(conversation_partner_emotion)
        p_emoji = p_info.get("emoji", "🤖")
        p_color = p_info.get("color", ansi_color(245))
        conv_part = (
            f"  {GRAY}│{RESET}  💬 "
            f"{p_color}{p_emoji} {conversation_partner}{RESET}"
        )

    print(
        f"  {DGRAY}{status_sym}{RESET} "
        f"{color}{BOLD}{emoji} {func_name}{RESET}"
        f"  {GRAY}│{RESET}"
        f"  cpu={SILVER}{cpu_ms:.2f}ms{RESET}"
        f"  avg={avg_color}{wall_ms:.1f}ms{RESET}"
        f"  error={err_color}{exception_count}{RESET}"
        f"  {GRAY}│{RESET}  feeling {color}{emotion}{RESET}"
        f"{conv_part}"
    )
