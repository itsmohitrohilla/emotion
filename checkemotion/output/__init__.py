"""emotion.output — terminal logging and dashboard display."""

from .logger       import say, say_registration, running, separator, say_evolution, print_metrics_row
from .dashboard    import show_dashboard
from .conversation import display_conversation

__all__ = [
    "say", "say_registration", "running", "separator",
    "say_evolution", "print_metrics_row",
    "show_dashboard",
    "display_conversation",
]
