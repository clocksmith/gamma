"""Hack2Hire 6916714410632c00111ca0f3 (Toy Language Grammar, variant 2 of 2) over an INFERRED spec; qualification unknown."""


def fmt(node):
    if isinstance(node, str):
        return node
    return '[' + ', '.join(fmt(child) for child in node) + ']'


def bind(param, arg, binding):
    if isinstance(param, str):
        if param[0] == 'T':
            text = fmt(arg)
            if param in binding:
                return binding[param] == text
            binding[param] = text
            return True
        return param == arg
    if not isinstance(arg, list) or len(arg) != len(param):
        return False
    for p, a in zip(param, arg):
        if not bind(p, a, binding):
            return False
    return True


def render(node, binding):
    if isinstance(node, str):
        return binding.get(node, node)
    return '[' + ', '.join(render(child, binding) for child in node) + ']'


def solve(params, returnType, args):
    if len(params) != len(args):
        return None
    binding = {}
    for p, a in zip(params, args):
        if not bind(p, a, binding):
            return None
    return render(returnType, binding)


class Solution:
    def inferReturnType(self, params, returnType, args):
        return solve(params, returnType, args)
