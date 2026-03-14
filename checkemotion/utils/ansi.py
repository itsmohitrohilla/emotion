from __future__ import annotations

ansi_color = lambda n: f"\033[38;5;{n}m"  # noqa: E731

RESET = "\033[0m"
BOLD  = "\033[1m"
DIM   = "\033[2m"

GREEN  = ansi_color(82)
YELLOW = ansi_color(220)
RED    = ansi_color(196)
CYAN   = ansi_color(87)
GRAY   = ansi_color(245)
WHITE  = ansi_color(255)
ORANGE = ansi_color(214)


def health_color(score: float) -> str:
    if score >= 80: return GREEN
    if score >= 50: return YELLOW
    return RED


def complexity_color(cc: float) -> str:
    if cc <= 2:  return GREEN
    if cc <= 5:  return YELLOW
    if cc <= 10: return ORANGE
    return RED


def bar(value: float, max_val: float, width: int = 12) -> str:
    if max_val <= 0:
        return f"{GRAY}{'░' * width}{RESET}"
    filled = min(int(round(value / max_val * width)), width)
    return f"{CYAN}{'█' * filled}{GRAY}{'░' * (width - filled)}{RESET}"
