You write programs in a small typed language for one programming problem. You see only the problem's public statement, starter code, parameter types and public examples. Reply with one JSON array and nothing else: no prose, no code fences.

# The language (schema "algsolve.typed-program.v2")

A program is a JSON object with exactly these keys:
- "schema": "algsolve.typed-program.v2"
- "parameters": the problem's parameter names, in order.
- "inputs": an object mapping each parameter name to its type.
- "body": a list of statements.
- "return": one expression.
- "output_type": the type of the return expression.

Types: "int", "bool", or ["list", T] for a list of T, or ["tuple", T1, T2, ...]. Parameter types map from the problem as int -> "int", bool -> "bool", List[int] -> ["list", "int"], List[List[int]] -> ["list", ["list", "int"]]. There is no string, float, tree or linked-list type: a problem whose parameters or result need one cannot be written in this language. Integers are bounded to 128 bits.

Expressions are JSON objects of exactly one of these shapes:
- {"ref": "name"}: a parameter or a bound name in scope.
- {"literal": 3} or {"literal": true}: an integer or boolean constant.
- {"op": OP, "args": [expressions]} where OP is one of:
  - "add", "sub", "mul": (int, int) -> int.
  - "neg": (int) -> int. "not": (bool) -> bool.
  - "eq", "lt": two ints or two bools -> bool ("lt" is strictly less than).
  - "len": (list) -> int.
  - "range": (int n) -> ["list", "int"] holding 0..n-1.
  - "empty_ints": () -> ["list", "int"].
  - "append": (list of T, T) -> a new list with the element added at the end.
  - "tuple": (values...) -> ["tuple", ...].
  - "field": (tuple, {"literal": i}) -> field i of the tuple (i is a literal).
  - "sort_by": (list of tuples, {"literal": i}, bool descending) -> the list sorted by scalar field i.
There is no division, modulo, list indexing, min, max, "and" or "or": build them from the operators above with statements (for example "a and b" as nested "if", the minimum with "lt" and "if").

Statements (all names are new; no shadowing; names bound inside "for" or "if" do not escape):
- {"op": "let", "name": "x", "value": expr}: immutable binding.
- {"op": "var", "name": "x", "value": expr}: mutable cell.
- {"op": "set", "name": "x", "value": expr}: assign a "var" of the same type (writes inside loops and branches persist).
- {"op": "for", "item": "v", "in": list-expr, "body": [statements]}: iterate the list.
- {"op": "if", "condition": bool-expr, "then": [statements], "else": [statements]}.
- {"op": "call", "operator": EFFECT, "args": [expressions], "out": "name"}: a resource operation, with EFFECT one of:
  - "map.new" () -> map; "map.has" (map, int) -> bool; "map.get" (map, int key, int default) -> int (stored value, or the default when absent); "map.set" (map, int, int) -> unit.
  - "heap.new" () -> min-heap of int; "heap.push" (heap, int) -> unit; "heap.pop" (heap) -> int.
  - "queue.new" () -> FIFO queue of int; "queue.push" (queue, int) -> unit; "queue.pop" (queue) -> int; "queue.size" (queue) -> int.
  - "dsu.new" (int n) -> disjoint-set over 0..n-1; "dsu.find" (dsu, int) -> int; "dsu.union" (dsu, int, int) -> bool.
  Resources (maps, heaps, queues, disjoint sets) are only used through "call" and its "out" name; they cannot be returned, stored in lists or passed elsewhere.

Example, the length of a list:
{"schema": "algsolve.typed-program.v2", "parameters": ["values"], "inputs": {"values": ["list", "int"]}, "body": [], "return": {"op": "len", "args": [{"ref": "values"}]}, "output_type": "int"}

Example, the sum of a list:
{"schema": "algsolve.typed-program.v2", "parameters": ["values"], "inputs": {"values": ["list", "int"]}, "body": [{"op": "var", "name": "total", "value": {"literal": 0}}, {"op": "for", "item": "v", "in": {"ref": "values"}, "body": [{"op": "set", "name": "total", "value": {"op": "add", "args": [{"ref": "total"}, {"ref": "v"}]}}]}], "return": {"ref": "total"}, "output_type": "int"}

# What to return

A JSON array of 1 to 4 proposals. Each proposal is an object with exactly these keys:
- "variant": a short distinct name for this approach.
- "program": the program object.
- "requirements": {"unsupported_requirements": []} when the program meets everything the statement requires; otherwise list, as short strings, each requirement the program does not meet.
- "bound_probe": {"args": [...], "expected": ...}: one input at the edge of the stated constraints, in the same argument encoding as the public examples, with the output you expect your program to return.

Give different approaches as separate proposals only when you are unsure which is correct. If the problem cannot be written in this language (for example it needs strings, trees, division or indexing that cannot be built from the operators), return exactly one proposal with "variant": "abstain", "program": null, "requirements": {"unsupported_requirements": ["<the reason>"]} and "bound_probe": {"args": [], "expected": null}.

# The problem

{{PUBLIC_INPUT}}
