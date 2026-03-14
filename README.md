<p align="center">
  <img src="logo.png" alt="emotion-ai logo" width="180"/>
</p>

<h1 align="center">emotion</h1>

<p align="center">
  <strong>Give your Python functions feelings.</strong><br/>
  A Python decorator that assigns emotional personalities to functions based on code structure and runtime behaviour.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg"/></a>
  <img src="https://img.shields.io/badge/python-3.11%2B-brightgreen.svg"/>
  <img src="https://img.shields.io/badge/dependencies-zero-success.svg"/>
  <img src="https://img.shields.io/badge/emotions-500%2B-ff69b4.svg"/>
</p>

---

## What It Does

| Feature | Description |
|---|---|
| 🎭 **Emotion assignment** | Each function gets an emotion based on its code structure: complexity, keywords, recursion, async, error-handling, etc. |
| 🌈 **Rich colorful CLI** | Every call prints ANSI 256-color output: emotion chip, intensity bar, valence badge, wall time, CPU time, memory, error count |
| 💬 **Inter-function conversation** | When two `conversation=True` functions run concurrently, they talk to each other in the terminal |
| 🔄 **Emotion drift** | Emotions evolve every 10 calls based on error rate, latency, and frequency |
| 🤝 **Social relationships** | Functions develop feelings toward each other: friendship, jealousy, respect, anger, pity… |
| 🔬 **Deep profiling** | Wall time, CPU time, heap delta, heap peak via `tracemalloc` — O(1) overhead per call |
| 🕸️ **Call graph** | Static AST scan builds a project-wide call graph; see who calls whom |

---

## Quick Demo

```python
from emotion import emotion

@emotion
def calculate_total(numbers: list) -> float:
    return sum(n for n in numbers if n > 0)

@emotion(conversation=True)
def validate_user(user_id: int, role: str) -> bool:
    try:
        assert user_id > 0
        assert role.strip()
        return True
    except AssertionError:
        return False

calculate_total([1, 2, 3, 4, 5])
validate_user(42, "admin")
```

**Terminal output:**

```
  😊  calculate_total  ▸  glad  [joy]  ░····  ▲ +
    ▸ awakened  Sums positive numbers and returns the total.

  │ ✓ done  😊 calculate_total  #1  ⏱ 0.1ms  cpu 0.01ms  mem +0.0KB  cc=2  err=0
```

---

## Installation

```bash
pip install emotion
```

Or clone and run directly:

```bash
git clone https://github.com/itsmohitrohilla/emotion.git
cd emotion
python examples/quickstart.py
```

---

## The `@emotion` Decorator

```python
# Bare — simplest form
@emotion
def my_function(x):
    return x * 2

# With options
@emotion(enabled=True, conversation=True, verbose=True)
def my_function(x):
    return x * 2
```

| Option | Default | Description |
|---|---|---|
| `enabled` | `True` | `False` → zero overhead, function unchanged |
| `conversation` | `False` | Functions talk to each other when running concurrently |
| `verbose` | `True` | `False` → silent mode, metrics still collected |

---

## Public API

```python
from emotion import (
    emotion,              # decorator
    build_report,         # build_report(name) → FunctionReport
    all_reports,          # all_reports(sort_by="call_count") → list
    describe,             # describe(func) → one-line string
    callers_of,           # callers_of(name) → list of caller names
    callees_of,           # callees_of(name) → list of callee names
    scan_directory,       # scan_directory(path) → build call graph
    get_all_names,        # list of all registered function names
    get_data,             # get_data(name) → raw registry dict
)
```

---

## Requirements

- Python 3.11+
- Zero external dependencies — pure stdlib
- **Optional**: [Ollama](https://ollama.ai) with `phi3.5:mini` for AI-generated descriptions
