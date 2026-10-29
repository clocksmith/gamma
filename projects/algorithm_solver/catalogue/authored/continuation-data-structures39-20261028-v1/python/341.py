"""Original frontend 341 variant; qualification unknown."""


def _is_int_elem(x):
    if hasattr(x, "isInteger"):
        return x.isInteger()
    return isinstance(x, int)


def _get_int_elem(x):
    if hasattr(x, "getInteger"):
        return x.getInteger()
    return x


def _get_list_elem(x):
    if hasattr(x, "getList"):
        return x.getList()
    return x


class NestedIterator:
    def __init__(self, nestedList):
        self.stack = list(reversed(nestedList))

    def next(self) -> int:
        self.hasNext()
        return _get_int_elem(self.stack.pop())

    def hasNext(self) -> bool:
        while self.stack:
            top = self.stack[-1]
            if _is_int_elem(top):
                return True
            self.stack.pop()
            sub = _get_list_elem(top)
            for item in reversed(sub):
                self.stack.append(item)
        return False


def solve(operation_names, argument_lists=None):
    if argument_lists is None:
        it = NestedIterator(operation_names)
        out = []
        while it.hasNext():
            out.append(it.next())
        return out
    instance = NestedIterator(argument_lists[0][0])
    out = [None]
    for op in operation_names[1:]:
        if op == "hasNext":
            out.append(instance.hasNext())
        elif op == "next":
            out.append(instance.next())
        else:
            raise ValueError("unknown operation")
    return out
