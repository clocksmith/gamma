"""Original frontend 1352 variant; qualification unknown."""


class ProductOfNumbers:
    def __init__(self):
        self.prefix = [1]

    def add(self, num: int) -> None:
        if num == 0:
            self.prefix = [1]
        else:
            self.prefix.append(self.prefix[-1] * num)

    def getProduct(self, k: int) -> int:
        if k >= len(self.prefix):
            return 0
        return self.prefix[-1] // self.prefix[-1 - k]


def solve(operation_names, argument_lists):
    inst = ProductOfNumbers()
    out = [None]
    for op, args in zip(operation_names[1:], argument_lists[1:]):
        if op == "add":
            inst.add(args[0])
            out.append(None)
        else:
            out.append(inst.getProduct(args[0]))
    return out
