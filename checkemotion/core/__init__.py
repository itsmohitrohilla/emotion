"""emotion.core — runtime engine: analysis, registry, profiling, decoration."""

from .decorator import emotion
from .registry  import (
    register, get_data, get_all_names,
    set_description, record_profile,
    record_call_start, record_call_end, record_co_call,
    update_relationships, compute_evolved_emotion, should_evolve,
)
from .analyzer  import extract_features, classify_emotion, is_method
from .profiler  import Profiler, ProfileSnapshot

__all__ = [
    "emotion",
    "register", "get_data", "get_all_names",
    "set_description", "record_profile",
    "record_call_start", "record_call_end", "record_co_call",
    "update_relationships", "compute_evolved_emotion", "should_evolve",
    "extract_features", "classify_emotion", "is_method",
    "Profiler", "ProfileSnapshot",
]
