"""Hack2Hire 69c19a8521f6ab4226964bf7 (Design Connect K Board) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class ConnectKGame:
    def __init__(self, k):
        self.k = k
        self.columns = {}  # column -> list whose last element is height 0 (bottom insertion is an append)

    def _cell(self, column, height):
        pieces = self.columns.get(column)
        if pieces is None or height < 0 or height >= len(pieces):
            return None
        return pieces[len(pieces) - 1 - height]

    def placePiece(self, player, column):
        pieces = self.columns.setdefault(column, [])
        pieces.append(player)
        k, height = self.k, len(pieces)
        run = 0
        for value in pieces:  # vertical runs live entirely inside this column
            run = run + 1 if value == player else 0
            if run >= k:
                return True
        for y in range(height):
            if pieces[height - 1 - y] != player:
                continue
            for dx, dy in ((1, 0), (1, 1), (1, -1)):
                count = 1
                for sign in (1, -1):
                    step = 1
                    while count < k and self._cell(column + sign * dx * step, y + sign * dy * step) == player:
                        count += 1
                        step += 1
                if count >= k:
                    return True
        return False


def solve(operation_names, argument_lists):
    if operation_names[0] != 'ConnectKGame' or len(argument_lists[0]) != 1:
        raise ValueError('exact initial constructor required')
    instance = ConnectKGame(*argument_lists[0])
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name != 'placePiece':
            raise ValueError('unknown method')
        result.append(instance.placePiece(*arguments))
    return result
