from __future__ import annotations

import functools
import inspect
import threading
from pathlib import Path
from typing import Callable, Optional

from . import analyzer, registry
from .profiler import Profiler
from ..analysis.call_graph import scan_directory
from ..analysis.narrator import describe
from ..output import logger

scan_lock = threading.Lock()
scan_done = False


def maybe_scan(func: Callable) -> None:
    global scan_done
    if scan_done:
        return
    with scan_lock:
        if scan_done:
            return
        try:
            source_file = inspect.getfile(func)
            scan_directory(Path(source_file).parent)
        except (TypeError, OSError):
            pass
        scan_done = True


active_calls_lock: threading.Lock = threading.Lock()
active_calls:      set[str]       = set()

conversation_funcs: set[str] = set()

conversation_queue_lock: threading.Lock                       = threading.Lock()
conversation_queue:      list[tuple[str, str, str, str, str]] = []
conversation_seen:       set[frozenset[str]]                  = set()


def flush_conversations() -> None:
    with conversation_queue_lock:
        items = list(conversation_queue)
        conversation_queue.clear()
    if not items:
        return
    try:
        from ..output.conversation import display_conversation
    except ImportError:
        return
    for func_a, emotion_a, func_b, emotion_b, relationship in items:
        display_conversation(func_a, emotion_a, func_b, emotion_b, relationship)


def emotion(
    decorated_func: Callable | None = None,
    *,
    enabled:        bool = True,
    conversation:   bool = False,
    verbose:        bool = True,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        if not enabled:
            return func

        maybe_scan(func)

        is_method_flag = analyzer.is_method(func)
        features       = analyzer.extract_features(func)
        initial_emotion = analyzer.classify_emotion(features, func.__name__, is_method_flag)

        qualified_name: str           = getattr(func, "__qualname__", func.__name__)
        class_name:     Optional[str] = (
            qualified_name.rsplit(".", 1)[0] if "." in qualified_name else None
        )

        registry.register(func.__name__, initial_emotion, features, is_method_flag, class_name)

        description = describe(func)
        registry.set_description(func.__name__, description)

        if verbose:
            logger.say_registration(initial_emotion, func.__name__, description)

        if conversation:
            conversation_funcs.add(func.__name__)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            function_name = func.__name__

            with active_calls_lock:
                concurrent_names = list(active_calls)
                active_calls.add(function_name)
            registry.record_co_call(function_name, concurrent_names)

            conv_partner_name:    str | None = None
            conv_partner_emotion: str | None = None
            if conversation:
                conv_partners = [n for n in concurrent_names if n in conversation_funcs]
                if conv_partners:
                    conv_partner_name    = conv_partners[0]
                    conv_partner_emotion = registry.get_data(conv_partner_name).get(
                        "emotion", "content"
                    )

            call_start_time  = registry.record_call_start(function_name)
            exception_raised = False
            result           = None

            profiler = Profiler()
            profiler.__enter__()
            try:
                result = func(*args, **kwargs)
            except Exception:
                exception_raised = True
                raise
            finally:
                profiler.__exit__(None, None, None)
                profile_snapshot = profiler.snapshot

                with active_calls_lock:
                    active_calls.discard(function_name)

                registry.record_call_end(function_name, call_start_time,
                                         exception=exception_raised)

                if profile_snapshot is not None:
                    registry.record_profile(
                        function_name,
                        wall_time_ms    = profile_snapshot.wall_time_ms,
                        cpu_time_ms     = profile_snapshot.cpu_time_ms,
                        memory_delta_kb = profile_snapshot.memory_delta_kb,
                        memory_peak_kb  = profile_snapshot.memory_peak_kb,
                    )

                registry.update_relationships(function_name)

                current_emotion = registry.get_data(function_name).get("emotion", initial_emotion)
                if registry.should_evolve(function_name):
                    evolved_emotion = registry.compute_evolved_emotion(
                        function_name, current_emotion
                    )
                    if evolved_emotion != current_emotion:
                        registry.REGISTRY[function_name]["emotion"] = evolved_emotion
                        current_emotion = evolved_emotion

                if verbose:
                    function_data         = registry.get_data(function_name)
                    call_count            = function_data.get("call_count", 0)
                    exception_count       = function_data.get("exception_count", 0)
                    cyclomatic_complexity = int(features[7])

                    wall_ms = profile_snapshot.wall_time_ms if profile_snapshot else function_data.get("average_time_ms", 0.0)
                    cpu_ms  = profile_snapshot.cpu_time_ms  if profile_snapshot else 0.0
                    mem_d   = profile_snapshot.memory_delta_kb if profile_snapshot else 0.0
                    mem_p   = profile_snapshot.memory_peak_kb  if profile_snapshot else 0.0
                    logger.print_metrics_row(
                        function_name,
                        current_emotion,
                        exception_raised             = exception_raised,
                        call_count                   = call_count,
                        wall_ms                      = wall_ms,
                        cpu_ms                       = cpu_ms,
                        mem_delta_kb                 = mem_d,
                        mem_peak_kb                  = mem_p,
                        cyclomatic_complexity        = cyclomatic_complexity,
                        exception_count              = exception_count,
                        conversation_partner         = conv_partner_name,
                        conversation_partner_emotion = conv_partner_emotion,
                    )

                    if conv_partner_name and conv_partner_emotion:
                        queue_conversation(function_name, current_emotion,
                                           conv_partner_name, conv_partner_emotion)

            return result

        wrapper.__emotional__    = True
        wrapper.__emotion__      = initial_emotion
        wrapper.__description__  = description
        wrapper.__features__     = features
        wrapper.__conversation__ = conversation
        return wrapper

    if decorated_func is not None:
        return decorator(decorated_func)
    return decorator


def queue_conversation(
    func_a: str, emotion_a: str, func_b: str, emotion_b: str
) -> None:
    pair_key = frozenset([func_a, func_b])
    with conversation_queue_lock:
        if pair_key in conversation_seen:
            return
        conversation_seen.add(pair_key)
        relationship = best_relationship(func_a, func_b)
        conversation_queue.append((func_a, emotion_a, func_b, emotion_b, relationship))


def trigger_conversation(
    func_name: str,
    partners:  list[str],
) -> None:
    try:
        from ..output.conversation import display_conversation
    except ImportError:
        return

    partner_name = partners[0]
    emotion_a    = registry.get_data(func_name).get("emotion",       "content")
    emotion_b    = registry.get_data(partner_name).get("emotion",    "content")
    relationship = best_relationship(func_name, partner_name)

    display_conversation(func_name, emotion_a, partner_name, emotion_b, relationship)


def best_relationship(name_a: str, name_b: str) -> str | None:
    top = registry.get_top_relationships(name_a, max_results=5)
    for other_name, rel_type in top:
        if other_name == name_b:
            return rel_type
    return None
