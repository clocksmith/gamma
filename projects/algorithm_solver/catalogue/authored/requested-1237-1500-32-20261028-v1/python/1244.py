"""Original frontend 1244 variant; qualification unknown."""


class Leaderboard:
    def __init__(self):
        self.scores = {}

    def addScore(self, playerId: int, score: int) -> None:
        self.scores[playerId] = self.scores.get(playerId, 0) + score

    def top(self, K: int) -> int:
        vals = sorted(self.scores.values(), reverse=True)
        return sum(vals[:K])

    def reset(self, playerId: int) -> None:
        self.scores.pop(playerId, None)


def solve(operation_names, argument_lists):
    inst = Leaderboard()
    out = [None]
    for op, args in zip(operation_names[1:], argument_lists[1:]):
        if op == "addScore":
            inst.addScore(args[0], args[1])
            out.append(None)
        elif op == "top":
            out.append(inst.top(args[0]))
        else:
            inst.reset(args[0])
            out.append(None)
    return out
