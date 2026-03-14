from __future__ import annotations

import ast
import inspect
import json
import textwrap
import urllib.error
import urllib.request
from typing import Optional

OLLAMA_GENERATE = "http://localhost:11434/api/generate"
OLLAMA_TAGS     = "http://localhost:11434/api/tags"

PREFERRED_MODELS = [
    "phi3.5:mini", "phi3:mini", "phi3:3.8b",
    "llama3.2:1b", "llama3.2:3b", "tinyllama",
    "mistral:7b-instruct-q2_K",
]

ollama_model: Optional[str] = None
ollama_checked: bool = False


def probe_ollama() -> Optional[str]:
    try:
        resp = urllib.request.urlopen(OLLAMA_TAGS, timeout=1)
        data = json.loads(resp.read())
        available: dict[str, str] = {
            m["name"].split(":")[0]: m["name"]
            for m in data.get("models", [])
        }
        for pref in PREFERRED_MODELS:
            base = pref.split(":")[0]
            if base in available:
                return available[base]
        first = data.get("models", [])
        if first:
            return first[0]["name"]
    except Exception:
        pass
    return None


def ollama_describe(source: str, func_name: str, model: str) -> Optional[str]:
    prompt = (
        "In exactly one concise plain-English sentence (no code, no bullet points), "
        "describe what this Python function does from a developer's perspective:\n\n"
        f"{source}\n\nOne sentence:"
    )
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": 100, "temperature": 0.1},
    }).encode()
    try:
        req = urllib.request.Request(
            OLLAMA_GENERATE, data=payload,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        resp = urllib.request.urlopen(req, timeout=8)
        text = json.loads(resp.read()).get("response", "").strip()
        if text:
            return text.split(".")[0].strip() + "."
    except Exception:
        pass
    return None


def infer_verb(name: str) -> str:
    n = name.lower()
    mapping = [
        (["get", "fetch", "load", "read", "retrieve", "find", "lookup"],    "Retrieves"),
        (["set", "put", "write", "save", "store", "persist", "push"],        "Stores"),
        (["create", "make", "build", "generate", "new", "produce", "forge"], "Creates"),
        (["delete", "remove", "drop", "clear", "destroy", "purge"],          "Removes"),
        (["update", "edit", "modify", "change", "patch", "mutate"],          "Updates"),
        (["check", "validate", "verify", "assert", "ensure", "is_", "has_"], "Validates"),
        (["parse", "decode", "extract", "analyze", "scan"],                  "Analyzes"),
        (["send", "emit", "publish", "notify", "dispatch", "broadcast"],     "Sends"),
        (["run", "execute", "process", "handle", "perform", "apply"],        "Executes"),
        (["init", "setup", "configure", "prepare", "bootstrap"],             "Initializes"),
        (["format", "render", "display", "print", "show", "log", "output"],  "Displays"),
        (["convert", "transform", "map", "translate", "encode"],             "Converts"),
        (["sort", "order", "rank", "prioritize"],                            "Sorts"),
        (["filter", "search", "query"],                                      "Searches"),
        (["calc", "compute", "sum", "count", "measure", "aggregate"],        "Computes"),
        (["listen", "watch", "subscribe", "poll", "wait"],                   "Watches"),
        (["connect", "join", "register", "bind", "attach"],                  "Connects"),
        (["close", "disconnect", "release", "shutdown", "stop"],             "Closes"),
    ]
    for keywords, verb in mapping:
        if any(k in n for k in keywords):
            return verb
    return "Processes"


def ast_describe(func) -> str:
    try:
        src = textwrap.dedent(inspect.getsource(func))
        tree = ast.parse(src)
    except (OSError, TypeError, SyntaxError):
        return "Processes data."

    fnodes = [n for n in ast.walk(tree)
              if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if not fnodes:
        return "Processes data."
    fn = fnodes[0]

    is_async      = isinstance(fn, ast.AsyncFunctionDef)
    params        = [p.arg for p in fn.args.args if p.arg not in ("self", "cls")]
    calls: list   = []
    returns_val   = False
    raises        = False
    yields        = False
    loops         = False
    conditions    = 0

    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.append(node.func.attr)
        elif isinstance(node, ast.Return) and node.value is not None:
            returns_val = True
        elif isinstance(node, ast.Raise):
            raises = True
        elif isinstance(node, (ast.Yield, ast.YieldFrom)):
            yields = True
        elif isinstance(node, (ast.For, ast.While)):
            loops = True
        elif isinstance(node, ast.If):
            conditions += 1

    verb = infer_verb(func.__name__)
    parts: list[str] = []

    if is_async:
        parts.append("Asynchronously")

    parts.append(verb)

    if params:
        if len(params) == 1:
            parts.append(f"the {params[0].replace('_', ' ')}")
        else:
            listed = ", ".join(p.replace("_", " ") for p in params[:3])
            parts.append(f"inputs ({listed})")

    if loops:
        parts.append("by iterating over items")

    if conditions > 2:
        parts.append("across multiple conditions")

    key_calls = [c for c in dict.fromkeys(calls) if not c.startswith("_")][:3]
    if key_calls:
        parts.append(f"using {', '.join(key_calls)}")

    if yields:
        parts.append("and yields results lazily")
    elif returns_val:
        parts.append("and returns the result")

    if raises:
        parts.append(", raising on invalid input")

    return " ".join(parts).rstrip(",") + "."


def describe(func) -> str:
    global ollama_model, ollama_checked

    if not ollama_checked:
        ollama_model = probe_ollama()
        ollama_checked = True

    if ollama_model:
        try:
            src = textwrap.dedent(inspect.getsource(func))
        except (OSError, TypeError):
            src = ""
        if src:
            result = ollama_describe(src, func.__name__, ollama_model)
            if result:
                return result

    return ast_describe(func)
