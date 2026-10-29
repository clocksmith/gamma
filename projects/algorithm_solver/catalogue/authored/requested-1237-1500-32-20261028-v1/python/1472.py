"""Original frontend 1472 variant; qualification unknown."""


class BrowserHistory:
    def __init__(self, homepage: str):
        self.hist = [homepage]
        self.curr = 0
        self.end = 0

    def visit(self, url: str) -> None:
        self.curr += 1
        if self.curr < len(self.hist):
            self.hist[self.curr] = url
        else:
            self.hist.append(url)
        self.end = self.curr

    def back(self, steps: int) -> str:
        self.curr = max(0, self.curr - steps)
        return self.hist[self.curr]

    def forward(self, steps: int) -> str:
        self.curr = min(self.end, self.curr + steps)
        return self.hist[self.curr]


def solve(operation_names, argument_lists):
    inst = BrowserHistory(argument_lists[0][0])
    out = [None]
    for op, args in zip(operation_names[1:], argument_lists[1:]):
        if op == "visit":
            inst.visit(args[0])
            out.append(None)
        elif op == "back":
            out.append(inst.back(args[0]))
        else:
            out.append(inst.forward(args[0]))
    return out
