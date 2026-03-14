from __future__ import annotations

import ast


def cyclomatic_complexity(tree: ast.AST) -> int:
    """McCabe cyclomatic complexity: count of independent execution paths."""
    count = 1
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                             ast.With, ast.Assert, ast.comprehension)):
            count += 1
        elif isinstance(node, ast.BoolOp):
            count += len(node.values) - 1
    return count


def nesting_depth(tree: ast.AST) -> int:
    """Maximum nesting depth of control-flow blocks in *tree*."""
    max_depth: list[int] = [0]

    def walk_node(node: ast.AST, depth: int) -> None:
        if isinstance(node, (ast.If, ast.While, ast.For, ast.With,
                             ast.Try, ast.FunctionDef, ast.AsyncFunctionDef)):
            max_depth[0] = max(max_depth[0], depth)
            for child in ast.iter_child_nodes(node):
                walk_node(child, depth + 1)
        else:
            for child in ast.iter_child_nodes(node):
                walk_node(child, depth)

    walk_node(tree, 1)
    return max_depth[0]


def has_recursion(func_name: str, tree: ast.AST) -> bool:
    """Return True if the function body contains a call to itself."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == func_name:
                return True
            if isinstance(node.func, ast.Attribute) and node.func.attr == func_name:
                return True
    return False


def has_heavy_computation(tree: ast.AST) -> bool:
    """Return True if the function contains ≥2 loop/comprehension constructs."""
    count = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.For, ast.While, ast.ListComp,
                             ast.GeneratorExp, ast.SetComp, ast.DictComp)):
            count += 1
    return count >= 2
