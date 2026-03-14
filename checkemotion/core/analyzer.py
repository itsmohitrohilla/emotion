"""analyzer.py — static AST feature extraction and emotion classification."""
from __future__ import annotations

import ast
import inspect
import textwrap

from ..schemas.emotions import EMOTIONS
from ..utils.ast_helpers import (
    cyclomatic_complexity as compute_cyclomatic,
    nesting_depth         as compute_nesting,
    has_recursion         as detect_recursion,
    has_heavy_computation as detect_heavy,
)


# ── Keyword flags (indices 10-14 in feature vector) ──────────────────────────
NAME_KEYWORD_FLAGS = {
    0: ["delete", "remove", "destroy", "drop", "kill", "purge", "wipe", "terminate", "abort"],
    1: ["get", "fetch", "read", "load", "receive", "pull", "retrieve", "query", "find"],
    2: ["create", "build", "make", "generate", "construct", "produce", "craft", "compose", "forge"],
    3: ["validate", "check", "verify", "assert", "ensure", "confirm", "inspect", "audit", "test"],
    4: ["log", "print", "display", "show", "render", "format", "output", "report", "emit", "debug"],
}


# ── Feature extraction ────────────────────────────────────────────────────────

def extract_features(func) -> list[float]:
    """Extract a 15-float feature vector from *func*.

    Indices
    -------
    0  branch_count          – if/for/while/except nodes
    1  line_count            – non-blank, non-decorator lines
    2  param_count           – all parameter kinds
    3  has_recursion         – 1.0 if self-call detected
    4  has_async             – 1.0 if async def
    5  has_try_except        – 1.0 if try block present
    6  has_yield             – 1.0 if yield/yield from present
    7  cyclomatic_complexity – McCabe score
    8  nesting_depth         – maximum control-flow depth
    9  return_count          – number of return statements
    10-14 name_flags         – keyword hint bitmask (5 emotion categories)

    Returns ``[0.0] * 15`` for builtins, lambdas, or unparseable sources.
    """
    try:
        src  = textwrap.dedent(inspect.getsource(func))
        tree = ast.parse(src)
    except (OSError, TypeError, SyntaxError):
        return [0.0] * 15

    func_node = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == func.__name__:
                func_node = node
                break
    if func_node is None:
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_node = node
                break
    if func_node is None:
        return [0.0] * 15

    branch_count = sum(
        1 for n in ast.walk(func_node)
        if isinstance(n, (ast.If, ast.For, ast.While, ast.ExceptHandler))
    )
    try:
        lines      = inspect.getsource(func).splitlines()
        line_count = len([l for l in lines if l.strip() and not l.strip().startswith("@")])
    except OSError:
        line_count = func_node.end_lineno - func_node.lineno + 1

    args        = func_node.args
    param_count = (len(args.args) + len(args.posonlyargs) +
                   len(args.kwonlyargs) + (1 if args.vararg else 0) +
                   (1 if args.kwarg else 0))

    has_recursion  = float(detect_recursion(func.__name__, func_node))
    has_async      = float(isinstance(func_node, ast.AsyncFunctionDef))
    has_try_except = float(any(isinstance(n, ast.Try) for n in ast.walk(func_node)))
    has_yield      = float(any(isinstance(n, (ast.Yield, ast.YieldFrom)) for n in ast.walk(func_node)))
    cyclomatic_score = compute_cyclomatic(func_node)
    nesting_score    = compute_nesting(func_node)
    return_count     = sum(1 for n in ast.walk(func_node) if isinstance(n, ast.Return))

    name_lower = func.__name__.lower()
    flags = [float(any(kw in name_lower for kw in NAME_KEYWORD_FLAGS[i])) for i in range(5)]

    return [
        float(branch_count), float(line_count), float(param_count),
        has_recursion, has_async, has_try_except, has_yield,
        float(cyclomatic_score), float(nesting_score), float(return_count),
    ] + flags


# ── Family scorer ─────────────────────────────────────────────────────────────

def score_families(features: list[float], name: str,
                   is_method_flag: bool) -> dict[str, float]:
    """Return a dict of family → score based on the 15-feature vector.

    Feature index reference
    -----------------------
    0  branch_count          7  cyclomatic_complexity
    1  line_count            8  nesting_depth
    2  param_count           9  return_count
    3  has_recursion         10 keyword_flag_dramatic
    4  has_async             11 keyword_flag_humble
    5  has_try_except        12 keyword_flag_excited
    6  has_yield             13 keyword_flag_nervous
                             14 keyword_flag_sarcastic
    """
    name_lower = name.lower()

    complexity = features[7] + features[8] + features[0] * 0.5
    simplicity = max(0.0, 15.0 - complexity)
    line_count = features[1]

    def has_keyword(*words: str) -> bool:
        return any(word in name_lower for word in words)

    family_scores: dict[str, float] = {}

    family_scores["joy"]            = features[12]*4 + simplicity*0.25 + has_keyword("init","setup","new","welcome")*2 - features[10]*2
    family_scores["serenity"]       = features[6]*4 + simplicity*0.5 - features[5]*0.5 - features[10]*2 + (features[0] < 3)*1.5
    family_scores["gratitude"]      = features[11]*4 + (line_count < 10)*2 + (features[2] <= 2)*1 + features[9]*0.4 + has_keyword("ack","thank","receive")*2
    family_scores["love"]           = is_method_flag*2 + features[2]*0.4 + has_keyword("send","notify","share","push","dispatch")*3
    family_scores["longing"]        = (5 < line_count < 30)*1.5 + (not any(features[10:15]))*1 + has_keyword("old","prev","last","hist","cache","legacy")*3
    family_scores["sadness"]        = (line_count < 8 and complexity < 3)*2 + has_keyword("fail","error","miss","none","null","empty")*2
    family_scores["disappointment"] = has_keyword("fail","invalid","none","missing","not_found","404")*3 + features[9]*0.5 + (features[0] > 0 and complexity < 5)*1
    family_scores["loneliness"]     = (line_count <= 5)*3 + (features[2] == 0)*2 + (features[9] == 0)*1 + (not is_method_flag)*0.5
    family_scores["fear"]           = features[5]*3 + features[8]*1.5 + has_keyword("danger","risk","unsafe","critical","panic","emergency")*3
    family_scores["anxiety"]        = features[13]*4 + features[5]*2 + features[7]*0.3 + (features[8] >= 2)*1 + has_keyword("retry","attempt","try","safe")*1
    family_scores["vulnerability"]  = (complexity < 5)*2 + features[5]*2 + (features[2] <= 2)*1.5 - features[12]*1
    family_scores["anger"]          = features[10]*6 + features[7]*0.4 + features[0]*0.3 + has_keyword("force","hard","override","abort","kill")*2
    family_scores["irritation"]     = features[0]*1.5 + (features[7] > 5)*2 + (features[8] > 2)*1 - features[12]*1 + has_keyword("handle","catch","wrap")*1
    family_scores["resentment"]     = has_keyword("reject","deny","block","revoke","ban","forbid")*3 + features[7]*0.4 + features[0]*0.4
    family_scores["jealousy"]       = (features[2] < 2 and features[7] > 4)*2 + has_keyword("compare","rank","score","vs","versus","beat")*3
    family_scores["disgust"]        = features[13]*2 + features[0]*0.5 + has_keyword("clean","filter","sanitize","strip","escape","encode")*3
    family_scores["surprise"]       = features[4]*4 + has_keyword("unexpected","sudden","random","event","hook","trigger","callback")*2 + (features[3] and features[4])*2
    family_scores["wonder"]         = features[3]*2 + has_keyword("explore","discover","search","find","scan","crawl","traverse")*3 + features[7]*0.2
    family_scores["anticipation"]   = features[12]*2 + features[4]*3 + has_keyword("wait","poll","watch","listen","subscribe","queue","schedule")*3
    family_scores["confidence"]     = features[2]*0.4 + features[12]*1.5 + features[9]*0.4 + (features[7] > 3 and features[8] < 4)*2 + has_keyword("run","execute","apply","do")*1
    family_scores["ambition"]       = line_count*0.05 + features[12]*2 + features[9]*0.5 + (line_count > 30)*2 + has_keyword("pipeline","workflow","orchestrate","manage")*2
    family_scores["accomplishment"] = features[9]*2 + has_keyword("complete","finish","done","result","output","return","resolve")*3 + (features[7] > 2)*1
    family_scores["humility"]       = features[11]*5 + (line_count < 15)*2 + (features[2] <= 3)*1 - features[10]*2 + has_keyword("helper","util","simple","basic")*2
    family_scores["intellectual"]   = features[7]*0.8 + features[13]*2 + has_keyword("analyze","compute","calc","process","parse","eval","solve")*3
    family_scores["creative"]       = features[12]*3 + (line_count > 20)*1.5 + has_keyword("generate","design","craft","compose","render","template")*3 + features[6]*1
    family_scores["confusion"]      = features[7]*0.5 + features[8]*1.5 + features[0]*0.8 - features[12]*1 - features[11]*1 + (complexity > 12)*2
    family_scores["indecision"]     = features[9]*1.5 + features[0]*0.8 + (not any(features[10:15]) and features[0] > 3)*2 + has_keyword("maybe","optional","fallback","default")*2
    family_scores["boredom"]        = features[14]*4 + (line_count < 5)*3 + (complexity < 2)*2 - features[12]*2 + has_keyword("noop","pass","stub","placeholder")*3
    family_scores["exhaustion"]     = line_count*0.06 + (line_count > 40)*2 + features[0]*0.4 - features[12]*1 + has_keyword("long","heavy","batch","bulk","all")*1
    family_scores["overwhelm"]      = features[7]*0.7 + features[8]*2 + features[0]*0.6 + (complexity > 15)*3 + (features[5] and features[0] > 5)*2
    family_scores["empowerment"]    = features[2]*0.8 + features[12]*2 + has_keyword("enable","allow","grant","unlock","authorize","activate")*3
    family_scores["belonging"]      = is_method_flag*4 + has_keyword("join","add","member","group","register","connect","bind")*3
    family_scores["betrayal"]       = features[10]*3 + has_keyword("override","replace","revoke","bypass","hijack","intercept","mock")*3 + features[5]*1.5
    family_scores["moral"]          = features[13]*3 + has_keyword("enforce","require","must","policy","rule","constraint","guard")*3
    family_scores["shame_deep"]     = has_keyword("fail","error","wrong","bad","invalid","broken","corrupt","oops")*3 + (complexity < 3)*2 - features[12]*2
    family_scores["existential"]    = features[3]*4 + (not any(features[10:15]) and features[7] > 5)*2 + has_keyword("self","meta","reflect","recurse","core","root")*2
    family_scores["power"]          = features[2]*1 + features[7]*0.5 + has_keyword("control","manage","admin","master","root","super","command")*3
    family_scores["humor"]          = features[14]*5 + has_keyword("debug","mock","fake","dummy","test","stub","joke","fun","random")*2
    family_scores["cultural"]       = has_keyword("transform","convert","translate","migrate","adapt","localize","encode","decode")*2 + (features[3] and features[6])*2
    family_scores["flow"]           = features[6]*5 + has_keyword("stream","pipe","chain","iter","yield","generate","next","flow")*3 + (3 < features[7] < 8)*1
    family_scores["spiritual"]      = features[3]*2 + features[6]*2 + has_keyword("soul","spirit","sacred","ritual","prayer","divine","eternal")*4
    family_scores["social_awkward"] = (is_method_flag and features[2] > 4)*2 + (features[5] and is_method_flag)*2 + has_keyword("callback","handler","middleware","intercept")*1
    family_scores["resilience"]     = features[5]*3 + features[3]*2 + has_keyword("retry","recover","restore","heal","backup","fallback","repair","fix")*3
    family_scores["complexity"]     = (features[7] > 10)*3 + (features[8] > 5)*2 + features[7]*0.3 + features[8]*0.5 - features[11]*1
    family_scores["numb"]           = (complexity < 1 and line_count <= 3 and not any(features[10:15]))*5 + (complexity < 2 and not any(features[10:15]))*2
    family_scores["hope"]           = features[12]*2 + has_keyword("init","start","begin","new","setup","boot","launch","open","create")*3 + (simplicity > 8)*1

    return family_scores


# ── Emotion classifier ────────────────────────────────────────────────────────

FAMILY_EMOTIONS: dict[str, list] = {}


def build_family_cache() -> None:
    for emotion_name, emotion_data in EMOTIONS.items():
        family_name = emotion_data["family"]
        if family_name not in FAMILY_EMOTIONS:
            FAMILY_EMOTIONS[family_name] = []
        FAMILY_EMOTIONS[family_name].append((emotion_name, emotion_data["intensity"]))
    for family_name in FAMILY_EMOTIONS:
        FAMILY_EMOTIONS[family_name].sort(key=lambda entry: entry[1])


def classify_emotion(features: list[float], func_name: str = "",
                     is_method: bool = False) -> str:
    if not FAMILY_EMOTIONS:
        build_family_cache()

    scores      = score_families(features, func_name, is_method)
    best_family = max(scores, key=scores.get)

    complexity  = features[7] + features[8] + features[0] * 0.5
    intensity   = min(5, max(1, int(complexity / 4) + 1))

    candidates  = FAMILY_EMOTIONS.get(best_family, [])
    if not candidates:
        return "content"

    return min(candidates, key=lambda x: abs(x[1] - intensity))[0]


# ── Utilities ─────────────────────────────────────────────────────────────────

def get_doc_lines(func) -> int:
    doc = inspect.getdoc(func)
    return len(doc.splitlines()) if doc else 0


def is_method(func) -> bool:
    """Heuristic: returns True if the first parameter is ``self`` or ``cls``."""
    try:
        params = list(inspect.signature(func).parameters.keys())
        return bool(params and params[0] in ("self", "cls"))
    except (ValueError, TypeError):
        return False
