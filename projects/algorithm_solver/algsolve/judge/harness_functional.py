"""In-sandbox harness for LeetCode-style callable solutions.

Reads /task/candidate.py and /task/calls.json (inputs only; expected values
never enter the sandbox), runs every call, and writes one JSON line per call
to the original stdout. The candidate's own prints go to stderr. The host
decides pass/fail by comparing these records with expected values it holds.

calls.json: {"entry": {"class": "Solution", "method": "twoSum"} | {"function": "f"},
             "calls": [{"args": [...], "kwargs": {...}}, ...]}
Typed values: {"__list_node__": [..]} and {"__tree_node__": [..]} are built
into ListNode / TreeNode before the call and serialized back the same way.
"""

import json
import os
import sys
import time

_OUT = os.fdopen(os.dup(1), "w", buffering=1)
os.dup2(2, 1)
sys.stdout = sys.stderr

PREAMBLE = """
from typing import *
import collections, heapq, bisect, math, itertools, functools, string, re, operator, random, sys
from collections import *
from heapq import *
from bisect import *
from math import *
from itertools import *
from functools import *
from string import *
from operator import *
# Convenience imports must not replace Python's modular exponentiation.
# Candidate code can still explicitly import a different pow itself.
from builtins import pow
inf = float('inf')

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
"""


def emit(record):
    _OUT.write(json.dumps(record, separators=(",", ":")) + "\n")


def build(value, ns):
    if isinstance(value, dict):
        if set(value) == {"__list_node__"}:
            head = None
            for item in reversed(value["__list_node__"]):
                head = ns["ListNode"](item, head)
            return head
        if set(value) == {"__tree_node__"}:
            items = value["__tree_node__"]
            if not items or items[0] is None:
                return None
            TreeNode = ns["TreeNode"]
            root = TreeNode(items[0])
            queue, i = [root], 1
            while queue and i < len(items):
                node = queue.pop(0)
                if i < len(items) and items[i] is not None:
                    node.left = TreeNode(items[i])
                    queue.append(node.left)
                i += 1
                if i < len(items) and items[i] is not None:
                    node.right = TreeNode(items[i])
                    queue.append(node.right)
                i += 1
            return root
        return {k: build(v, ns) for k, v in value.items()}
    if isinstance(value, list):
        return [build(v, ns) for v in value]
    return value


def dump(value, ns, depth=0):
    if depth > 200:
        raise ValueError("result nesting too deep")
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            return {"__float__": repr(value)}
        return value
    if isinstance(value, ns["ListNode"]):
        out, seen = [], 0
        while value is not None:
            seen += 1
            if seen > 1_000_000:
                raise ValueError("list cycle or excessive length")
            out.append(dump(value.val, ns, depth + 1))
            value = value.next
        return {"__list_node__": out}
    if isinstance(value, ns["TreeNode"]):
        out, queue = [], [value]
        while queue:
            node = queue.pop(0)
            if node is None:
                out.append(None)
                continue
            out.append(dump(node.val, ns, depth + 1))
            queue.append(node.left)
            queue.append(node.right)
            if len(out) > 1_000_000:
                raise ValueError("tree too large")
        while out and out[-1] is None:
            out.pop()
        return {"__tree_node__": out}
    if isinstance(value, (list, tuple)):
        return [dump(v, ns, depth + 1) for v in value]
    if isinstance(value, (set, frozenset)):
        return {"__set__": sorted((dump(v, ns, depth + 1) for v in value), key=repr)}
    if isinstance(value, dict):
        pairs = [[dump(k, ns, depth + 1), dump(v, ns, depth + 1)] for k, v in value.items()]
        return {"__dict__": sorted(pairs, key=lambda kv: json.dumps(kv[0], sort_keys=True))}
    raise TypeError(f"unsupported result type {type(value).__name__}")


def main():
    with open("/task/calls.json", encoding="utf-8") as handle:
        spec = json.load(handle)
    with open("/task/candidate.py", encoding="utf-8") as handle:
        source = handle.read()
    ns = {"__name__": "candidate"}
    exec(compile(PREAMBLE, "preamble.py", "exec"), ns)
    try:
        exec(compile(source, "candidate.py", "exec"), ns)
    except BaseException as exc:  # report and stop; host fails every call
        emit({"load_error": type(exc).__name__, "detail": str(exc)[:500]})
        return
    entry = spec["entry"]
    for index, call in enumerate(spec["calls"]):
        record = {"i": index}
        started = time.perf_counter()
        try:
            if "class" in entry:
                target = getattr(ns[entry["class"]](), entry["method"])
            else:
                target = ns[entry["function"]]
            args = [build(a, ns) for a in call.get("args", [])]
            kwargs = {k: build(v, ns) for k, v in call.get("kwargs", {}).items()}
            result = target(*args, **kwargs)
            record["result"] = dump(result, ns)
            record["args_after"] = [dump(a, ns) for a in args]
            record["kwargs_after"] = {k: dump(v, ns) for k, v in kwargs.items()}
        except RecursionError:
            record["error"] = "RecursionError"
        except BaseException as exc:
            record["error"] = type(exc).__name__
            record["detail"] = str(exc)[:300]
        record["seconds"] = round(time.perf_counter() - started, 6)
        emit(record)
    emit({"done": len(spec["calls"])})


if __name__ == "__main__":
    sys.setrecursionlimit(100000)
    main()
