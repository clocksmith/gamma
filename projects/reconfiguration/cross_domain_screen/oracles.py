"""CPU-only screen evaluator. Generated Python is interpreted, never exec/eval'd."""
import argparse
import ast
import copy
from fractions import Fraction
import json
import operator
from pathlib import Path
import sys


class Invalid(ValueError):
    pass


BUILTIN_NAMES = {"len", "range", "enumerate", "zip", "min", "max", "sorted",
                 "list", "tuple", "abs", "sum", "reversed"}


def exact_equal(actual, expected):
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, (list, tuple)):
        return len(actual) == len(expected) and all(exact_equal(a, b) for a, b in zip(actual, expected))
    if isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(exact_equal(actual[k], expected[k]) for k in expected)
    return actual == expected


class BoundedPython:
    """Small explicit language for the two declared function contracts."""

    def __init__(self, source, name, arity):
        if len(source) > 12000:
            raise Invalid("source size limit")
        tree = ast.parse(source)
        if len(list(ast.walk(tree))) > 1500:
            raise Invalid("AST size limit")
        if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
            raise Invalid("exactly one function required")
        self.fn = tree.body[0]
        args = self.fn.args
        if self.fn.name != name or len(args.args) != arity or any((args.defaults, args.kw_defaults, args.kwonlyargs, args.posonlyargs, args.vararg, args.kwarg, self.fn.decorator_list, self.fn.returns)) or any(a.annotation or a.arg in BUILTIN_NAMES for a in args.args):
            raise Invalid("function signature mismatch")
        allowed = (ast.Module, ast.FunctionDef, ast.arguments, ast.arg, ast.Load, ast.Store,
                   ast.Constant, ast.Name, ast.List, ast.Tuple, ast.Subscript, ast.Slice,
                   ast.Assign, ast.AugAssign, ast.Return, ast.For, ast.While, ast.If,
                   ast.Expr, ast.Pass, ast.Break, ast.Continue, ast.BinOp, ast.UnaryOp,
                   ast.BoolOp, ast.Compare, ast.IfExp, ast.Call, ast.Attribute,
                   ast.ListComp, ast.comprehension, ast.Add, ast.Sub, ast.Mult,
                   ast.FloorDiv, ast.Mod, ast.USub, ast.UAdd, ast.Not, ast.And, ast.Or,
                   ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.In, ast.NotIn)
        for node in ast.walk(tree):
            if not isinstance(node, allowed):
                raise Invalid("unsupported syntax: " + type(node).__name__)
            if isinstance(node, ast.Name) and node.id.startswith("_"):
                raise Invalid("private names forbidden")
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and node.id in BUILTIN_NAMES:
                raise Invalid("builtin shadowing forbidden")
            if isinstance(node, ast.Attribute) and node.attr != "append":
                raise Invalid("only list.append attributes allowed")
            if isinstance(node, ast.Call) and (node.keywords or not isinstance(node.func, (ast.Name, ast.Attribute))):
                raise Invalid("unsupported call")
        self.steps = 0

    def tick(self):
        self.steps += 1
        if self.steps > 20000:
            raise Invalid("interpreter step limit")

    def checked(self, value):
        if isinstance(value, int) and value.bit_length() > 128:
            raise Invalid("integer size limit")
        if isinstance(value, (list, tuple, str, range)) and len(value) > 1000:
            raise Invalid("container size limit")
        return value

    def expr(self, n, env):
        self.tick()
        if isinstance(n, ast.Constant):
            if type(n.value) not in (int, bool, str, type(None)):
                raise Invalid("unsupported constant")
            return self.checked(n.value)
        if isinstance(n, ast.Name):
            return env[n.id]
        if isinstance(n, (ast.List, ast.Tuple)):
            result = [self.expr(x, env) for x in n.elts]
            return self.checked(result if isinstance(n, ast.List) else tuple(result))
        if isinstance(n, ast.Subscript):
            return self.expr(n.value, env)[self.expr(n.slice, env)]
        if isinstance(n, ast.Slice):
            return slice(*(self.expr(x, env) if x else None for x in (n.lower, n.upper, n.step)))
        if isinstance(n, ast.BinOp):
            left, right = self.expr(n.left, env), self.expr(n.right, env)
            if isinstance(n.op, ast.Mult):
                for seq, count in ((left, right), (right, left)):
                    if isinstance(seq, (list, tuple, str)) and isinstance(count, int) and len(seq) * max(0, count) > 1000:
                        raise Invalid("container size limit")
            ops = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
                   ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod}
            return self.checked(ops[type(n.op)](left, right))
        if isinstance(n, ast.UnaryOp):
            return self.checked({ast.USub: operator.neg, ast.UAdd: operator.pos, ast.Not: operator.not_}[type(n.op)](self.expr(n.operand, env)))
        if isinstance(n, ast.BoolOp):
            for item in n.values:
                result = self.expr(item, env)
                if isinstance(n.op, ast.And) and not result or isinstance(n.op, ast.Or) and result:
                    return result
            return result
        if isinstance(n, ast.Compare):
            left = self.expr(n.left, env)
            ops = {ast.Eq: operator.eq, ast.NotEq: operator.ne, ast.Lt: operator.lt,
                   ast.LtE: operator.le, ast.Gt: operator.gt, ast.GtE: operator.ge,
                   ast.In: lambda a, b: a in b, ast.NotIn: lambda a, b: a not in b}
            for op, part in zip(n.ops, n.comparators):
                right = self.expr(part, env)
                if not ops[type(op)](left, right):
                    return False
                left = right
            return True
        if isinstance(n, ast.IfExp):
            return self.expr(n.body if self.expr(n.test, env) else n.orelse, env)
        if isinstance(n, ast.Call):
            args = [self.expr(a, env) for a in n.args]
            if isinstance(n.func, ast.Attribute):
                value = self.expr(n.func.value, env)
                if not isinstance(value, list) or len(args) != 1 or len(value) >= 1000:
                    raise Invalid("invalid append")
                value.append(args[0])
                return None
            functions = {"len": len, "range": range, "enumerate": lambda x: list(enumerate(x)),
                         "zip": lambda *x: list(zip(*x)), "min": min, "max": max,
                         "sorted": sorted, "list": list, "tuple": tuple, "abs": abs,
                         "sum": sum, "reversed": lambda x: list(reversed(x))}
            if n.func.id not in functions:
                raise Invalid("call not allowed: " + n.func.id)
            return self.checked(functions[n.func.id](*args))
        if isinstance(n, ast.ListComp):
            result = []
            def visit(index, scope):
                self.tick()
                if index == len(n.generators):
                    result.append(self.expr(n.elt, scope))
                    self.checked(result)
                    return
                gen = n.generators[index]
                if gen.is_async:
                    raise Invalid("async forbidden")
                for value in self.expr(gen.iter, scope):
                    self.tick()
                    nested = dict(scope)
                    self.assign(gen.target, value, nested)
                    if all(self.expr(test, nested) for test in gen.ifs):
                        visit(index + 1, nested)
            visit(0, dict(env))
            return result
        raise Invalid("unsupported expression: " + type(n).__name__)

    def assign(self, target, value, env):
        self.tick()
        if isinstance(target, ast.Name):
            env[target.id] = value
        elif isinstance(target, (ast.Tuple, ast.List)):
            if len(target.elts) != len(value):
                raise Invalid("unpack mismatch")
            for part, item in zip(target.elts, value):
                self.assign(part, item, env)
        elif isinstance(target, ast.Subscript):
            self.expr(target.value, env)[self.expr(target.slice, env)] = value
        else:
            raise Invalid("unsupported assignment")

    def block(self, statements, env):
        for n in statements:
            self.tick()
            if isinstance(n, ast.Return):
                return ("return", self.expr(n.value, env) if n.value else None)
            if isinstance(n, ast.Assign):
                value = self.expr(n.value, env)
                for target in n.targets:
                    self.assign(target, value, env)
            elif isinstance(n, ast.AugAssign):
                value = self.expr(ast.BinOp(left=n.target, op=n.op, right=n.value), env)
                self.assign(n.target, value, env)
            elif isinstance(n, ast.Expr):
                self.expr(n.value, env)
            elif isinstance(n, ast.If):
                result = self.block(n.body if self.expr(n.test, env) else n.orelse, env)
                if result:
                    return result
            elif isinstance(n, (ast.For, ast.While)):
                iterator = iter(self.expr(n.iter, env)) if isinstance(n, ast.For) else None
                broken = False
                while True:
                    self.tick()
                    if iterator is not None:
                        try:
                            self.assign(n.target, next(iterator), env)
                        except StopIteration:
                            break
                    elif not self.expr(n.test, env):
                        break
                    result = self.block(n.body, env)
                    if result and result[0] == "return":
                        return result
                    if result and result[0] == "break":
                        broken = True
                        break
                if not broken:
                    result = self.block(n.orelse, env)
                    if result:
                        return result
            elif isinstance(n, ast.Break):
                return ("break", None)
            elif isinstance(n, ast.Continue):
                return ("continue", None)
            elif not isinstance(n, ast.Pass):
                raise Invalid("unsupported statement")
        return None

    def call(self, arguments):
        self.steps = 0
        args = copy.deepcopy(arguments)
        env = dict(zip((a.arg for a in self.fn.args.args), args))
        result = self.block(self.fn.body, env)
        if args != arguments:
            raise Invalid("input mutation")
        return result[1] if result and result[0] == "return" else None


PYTHON_CASES = {
    "python-runs": {
        "name": "compress_runs", "arity": 1,
        "public": [([[4, 4, 9]], [[4, 2], [9, 1]])],
        "heldout": [([[]], []), ([[2, 2, 2]], [[2, 3]]),
                    ([[1, 2, 1]], [[1, 1], [2, 1], [1, 1]]),
                    ([[-2, -2, 0, 0, 0, 8]], [[-2, 2], [0, 3], [8, 1]])]},
    "python-intervals": {
        "name": "intersect_intervals", "arity": 2,
        "public": [([[[1, 4]], [[3, 7]]], [[3, 4]])],
        "heldout": [([[], [[1, 2]]], []), ([ [[1, 2]], []], []),
                    ([[[1, 3]], [[3, 5]]], [[3, 3]]),
                    ([[[0, 2], [5, 9]], [[1, 6], [8, 12]]], [[1, 2], [5, 6], [8, 9]]),
                    ([[[-8, -3], [2, 4]], [[-6, -5], [-2, 1], [3, 8]]], [[-6, -5], [3, 4]])]}}


def exact_answers(task_id):
    if task_id == "arithmetic-fractions":
        values = [(Fraction(137, 12) - Fraction(49, 18)) * 36,
                  (Fraction(7, 8) + Fraction(11, 12)) * 48,
                  (Fraction(23, 15) - Fraction(2, 9)) * 45]
        assert all(v.denominator == 1 for v in values)
        return [int(v) for v in values]
    if task_id == "arithmetic-congruences":
        return [next(x for x in range(m * n) if x % m == a and x % n == b)
                for m, a, n, b in [(17, 5, 23, 8), (11, 7, 13, 4), (7, 3, 19, 11)]]
    if task_id == "text-records":
        rows = [line.split("|") for line in "b7|keep|9|Lima\na2|drop|1|Oslo\nc4|keep|2|Kyoto\na1|keep|9|Accra\ne8|keep|2|Bern".splitlines()]
        return [{"id": row[0].upper(), "city": row[3]} for row in
                sorted((r for r in rows if r[1] == "keep"), key=lambda r: (int(r[2]), r[0]))]
    if task_id == "text-escape":
        data = r"al\|pha|be\\ta||ga\|mma\\"
        result, field, escaped = [], "", False
        for char in data:
            if escaped:
                field += char
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == "|":
                result.append(field)
                field = ""
            else:
                field += char
        assert not escaped
        return result + [field]
    raise Invalid("unknown task")


def score(task_id, source, phase="both"):
    if phase not in ("public", "heldout", "both"):
        raise Invalid("unknown phase")
    checks = []
    phases = ("public", "heldout") if phase == "both" else (phase,)
    try:
        if task_id in PYTHON_CASES:
            spec = PYTHON_CASES[task_id]
            interpreter = BoundedPython(source, spec["name"], spec["arity"])
            for part in phases:
                for index, (args, expected) in enumerate(spec[part]):
                    try:
                        actual = interpreter.call(args)
                        passed = exact_equal(actual, expected)
                        checks.append({"id": f"{part}-{index}", "phase": part, "passed": passed})
                    except Exception as error:
                        checks.append({"id": f"{part}-{index}", "phase": part, "passed": False, "error": type(error).__name__ + ": " + str(error)})
        else:
            if len(source) > 12000:
                raise Invalid("source size limit")
            actual = json.loads(source)
            if task_id.startswith("arithmetic-"):
                schema = type(actual) is list and len(actual) == 3 and all(type(x) is int for x in actual)
            elif task_id == "text-records":
                schema = type(actual) is list and all(type(x) is dict and set(x) == {"id", "city"} and all(type(v) is str for v in x.values()) for x in actual)
            elif task_id == "text-escape":
                schema = type(actual) is list and all(type(x) is str for x in actual)
            else:
                raise Invalid("unknown task")
            if "public" in phases:
                checks.append({"id": "public-schema", "phase": "public", "passed": schema})
            if "heldout" in phases:
                checks.append({"id": "heldout-exact", "phase": "heldout", "passed": schema and actual == exact_answers(task_id)})
        result = {"taskId": task_id, "phase": phase, "passed": bool(checks) and all(c["passed"] for c in checks), "checks": checks}
        for part in phases:
            result[part + "Passed"] = all(c["passed"] for c in checks if c["phase"] == part)
        return result
    except Exception as error:
        return {"taskId": task_id, "phase": phase, "passed": False, "checks": checks,
                **{p + "Passed": False for p in phases}, "error": type(error).__name__ + ": " + str(error)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id")
    parser.add_argument("--source-file", type=Path)
    parser.add_argument("--phase", choices=["public", "heldout", "both"], default="both")
    args = parser.parse_args()
    if args.task_id and args.source_file:
        request = {"taskId": args.task_id, "source": args.source_file.read_text(), "phase": args.phase}
    elif not args.task_id and not args.source_file:
        request = json.load(sys.stdin)
    else:
        parser.error("--task-id and --source-file must be supplied together")
    print(json.dumps(score(request["taskId"], request["source"], request.get("phase", "both")), sort_keys=True))


if __name__ == "__main__":
    main()
