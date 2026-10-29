"""Original frontend 1286 variant; qualification unknown."""


class CombinationIterator:
    def __init__(self, characters: str, combinationLength: int):
        self.chars = characters
        self.n = len(characters)
        self.k = combinationLength
        self.idx = list(range(combinationLength))
        self.has_more = True

    def next(self) -> str:
        res = "".join(self.chars[i] for i in self.idx)
        i = self.k - 1
        while i >= 0 and self.idx[i] == self.n - self.k + i:
            i -= 1
        if i < 0:
            self.has_more = False
        else:
            self.idx[i] += 1
            for j in range(i + 1, self.k):
                self.idx[j] = self.idx[j - 1] + 1
        return res

    def hasNext(self) -> bool:
        return self.has_more


def solve(operation_names, argument_lists):
    inst = CombinationIterator(argument_lists[0][0], argument_lists[0][1])
    out = [None]
    for op in operation_names[1:]:
        if op == "next":
            out.append(inst.next())
        else:
            out.append(inst.hasNext())
    return out
