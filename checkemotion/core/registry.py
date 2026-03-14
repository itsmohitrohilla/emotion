from __future__ import annotations

import time
from threading import Lock

registry_lock = Lock()
REGISTRY: dict = {}


def register(
    name: str,
    emotion: str,
    features: list,
    is_method_flag: bool,
    class_name: str = None,
) -> None:
    with registry_lock:
        if name not in REGISTRY:
            REGISTRY[name] = {
                "emotion": emotion,
                "features": features,
                "is_method": is_method_flag,
                "class_name": class_name,
                "call_count": 0,
                "exception_count": 0,
                "total_time_ms": 0.0,
                "average_time_ms": 0.0,
                "last_called": None,
                "cocall_counts": {},
                "recent_calls": [],
                "recent_exceptions": [],
                "relationships": {},
                "description": "",
                "profile_history": [],
            }


def set_description(name: str, description: str) -> None:
    with registry_lock:
        if name in REGISTRY:
            REGISTRY[name]["description"] = description


def record_profile(
    name: str,
    wall_time_ms: float,
    cpu_time_ms: float,
    memory_delta_kb: float,
    memory_peak_kb: float,
) -> None:
    with registry_lock:
        if name not in REGISTRY:
            return
        profile_history_list = REGISTRY[name]["profile_history"]
        profile_history_list.append(
            {
                "wall_time_ms": wall_time_ms,
                "cpu_time_ms": cpu_time_ms,
                "memory_delta_kb": memory_delta_kb,
                "memory_peak_kb": memory_peak_kb,
            }
        )
        if len(profile_history_list) > 50:
            profile_history_list.pop(0)


def record_call_start(name: str) -> float:
    with registry_lock:
        if name not in REGISTRY:
            return time.time()
        REGISTRY[name]["call_count"] += 1
        call_timestamp = time.time()
        REGISTRY[name]["last_called"] = call_timestamp
        recent_calls_list = REGISTRY[name]["recent_calls"]
        recent_calls_list.append(call_timestamp)
        if len(recent_calls_list) > 20:
            recent_calls_list.pop(0)
        return call_timestamp


def record_call_end(name: str, start_time: float, exception: bool = False) -> float:
    elapsed_ms = (time.time() - start_time) * 1000
    with registry_lock:
        if name not in REGISTRY:
            return elapsed_ms
        function_data = REGISTRY[name]
        function_data["total_time_ms"] += elapsed_ms
        if function_data["call_count"] > 0:
            function_data["average_time_ms"] = (
                function_data["total_time_ms"] / function_data["call_count"]
            )
        if exception:
            function_data["exception_count"] += 1
            function_data["recent_exceptions"].append(time.time())
            if len(function_data["recent_exceptions"]) > 20:
                function_data["recent_exceptions"].pop(0)
    return elapsed_ms


def record_co_call(caller: str, concurrent_names: list) -> None:
    with registry_lock:
        if caller not in REGISTRY:
            return
        for other_name in concurrent_names:
            if other_name == caller or other_name not in REGISTRY:
                continue
            cocall_counter = REGISTRY[caller]["cocall_counts"]
            cocall_counter[other_name] = cocall_counter.get(other_name, 0) + 1


def update_relationships(name: str) -> None:
    with registry_lock:
        if name not in REGISTRY:
            return
        function_data = REGISTRY[name]
        my_features = function_data["features"]
        my_complexity = my_features[7]
        my_call_count = function_data["call_count"]
        my_exception_count = function_data["exception_count"]

        relationships: dict = {}
        for other_name, other_function_data in REGISTRY.items():
            if other_name == name:
                continue
            their_complexity = other_function_data["features"][7]
            their_call_count = other_function_data["call_count"]
            cocall_count = function_data["cocall_counts"].get(other_name, 0)

            if cocall_count >= 3:
                relationships[other_name] = "friendship"
                continue

            if other_function_data["exception_count"] >= 2 and my_exception_count >= 1:
                relationships[other_name] = "anger"
                continue
            if (
                their_call_count > 0
                and my_call_count > 0
                and their_call_count >= my_call_count * 3
            ):
                relationships[other_name] = "jealousy"
                continue

            if their_complexity >= my_complexity * 1.5 and their_complexity > 3:
                relationships[other_name] = "respect"
                continue

            if my_complexity > 2 and their_complexity < my_complexity * 0.6:
                relationships[other_name] = "mock"
                continue

            if their_call_count <= 2 and other_function_data["features"][1] <= 5:
                relationships[other_name] = "pity"
                continue

            if abs(their_complexity - my_complexity) >= 5:
                relationships[other_name] = "confusion"
                continue

            if other_function_data["is_method"] and other_function_data["class_name"]:
                relationships[other_name] = "class_respect"
                continue

        function_data["relationships"] = relationships


def get_top_relationships(name: str, max_results: int = 2) -> list:
    relationship_priority = {
        "anger": 7,
        "friendship": 6,
        "jealousy": 5,
        "respect": 4,
        "mock": 3,
        "pity": 2,
        "confusion": 1,
        "class_respect": 0,
    }
    with registry_lock:
        if name not in REGISTRY:
            return []
        relationships = REGISTRY[name]["relationships"]
        if not relationships:
            return []
        sorted_relationships = sorted(
            relationships.items(),
            key=lambda relationship_item: relationship_priority.get(
                relationship_item[1], 0
            ),
            reverse=True,
        )
        return sorted_relationships[:max_results]


def get_data(name: str) -> dict:
    with registry_lock:
        return dict(REGISTRY.get(name, {}))


def get_all_names() -> list:
    with registry_lock:
        return list(REGISTRY.keys())


def should_evolve(name: str) -> bool:
    with registry_lock:
        if name not in REGISTRY:
            return False
        call_count = REGISTRY[name]["call_count"]
        return call_count % 10 == 0 and call_count > 0


def compute_evolved_emotion(name: str, current_emotion: str) -> str:
    with registry_lock:
        if name not in REGISTRY:
            return current_emotion
        function_data = REGISTRY[name]
        call_count = function_data["call_count"]
        exception_count = function_data["exception_count"]
        average_time_ms = function_data["average_time_ms"]
        recent_call_count = len(function_data["recent_calls"])

    exception_rate = exception_count / max(call_count, 1)

    if exception_rate > 0.3:
        return "angry" if current_emotion != "angry" else "grumpy"
    if average_time_ms > 500:
        return "overwhelmed" if current_emotion != "overwhelmed" else "dramatic"
    if call_count >= 50:
        return "nostalgic"
    if call_count >= 20:
        return "bold"
    if recent_call_count == 0:
        return "lonely"
    return current_emotion
