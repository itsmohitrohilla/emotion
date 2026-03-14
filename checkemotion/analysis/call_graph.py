from __future__ import annotations

import ast
import os
import threading
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set

call_graph_lock = threading.Lock()
CALL_GRAPH:    Dict[str, Set[str]] = defaultdict(set)
REVERSE_GRAPH: Dict[str, Set[str]] = defaultdict(set)
SCANNED_DIRS:  Set[str] = set()


def callees_in_func(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> Set[str]:
    found: Set[str] = set()
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                found.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                found.add(node.func.attr)
    return found


def scan_directory(directory: str | Path) -> None:
    directory = str(Path(directory).resolve())
    with call_graph_lock:
        if directory in SCANNED_DIRS:
            return
        SCANNED_DIRS.add(directory)

    for root, _, files in os.walk(directory):
        for fname in files:
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(root, fname)
            try:
                source = Path(fpath).read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(source, filename=fpath)
            except (SyntaxError, OSError, ValueError):
                continue

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    caller = node.name
                    for callee in callees_in_func(node):
                        if callee == caller:
                            continue
                        with call_graph_lock:
                            CALL_GRAPH[caller].add(callee)
                            REVERSE_GRAPH[callee].add(caller)


def callers_of(name: str) -> List[str]:
    with call_graph_lock:
        return sorted(REVERSE_GRAPH.get(name, set()))


def callees_of(name: str) -> List[str]:
    with call_graph_lock:
        return sorted(CALL_GRAPH.get(name, set()))


def centrality(name: str) -> int:
    with call_graph_lock:
        return len(REVERSE_GRAPH.get(name, set()))


def is_central(name: str, threshold: int = 3) -> bool:
    return centrality(name) >= threshold


def call_depth(name: str, max_depth: int = 6) -> int:
    visited: Set[str] = set()
    queue = [(name, 0)]
    max_seen = 0
    while queue:
        cur, depth = queue.pop(0)
        if cur in visited or depth > max_depth:
            continue
        visited.add(cur)
        max_seen = max(max_seen, depth)
        with call_graph_lock:
            children = list(CALL_GRAPH.get(cur, set()))
        for child in children:
            queue.append((child, depth + 1))
    return max_seen
