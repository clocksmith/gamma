"""Hack2Hire 6ac95215339e3a32c154ddc3 (Design a Rectangle Board, level 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class RectangleBoard:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # per-id parallel lists (index = id); inactive ids stay in place and are skipped
        self.boxes = [(0, 0, -1, -1)]  # id 0 placeholder: empty box, never active
        self.key = [0]
        self.active = [False]
        self.next_key = 0
        self.history = []

    def _is_active(self, rid):
        return type(rid) is int and 1 <= rid < len(self.active) and self.active[rid]

    def addRectangle(self, x1, y1, x2, y2):
        rid = len(self.active)
        self.next_key += 1
        self.boxes.append((x1, y1, x2, y2))
        self.key.append(self.next_key)
        self.active.append(True)
        self.history.append(('add', rid, None))
        return rid

    def getTopRectangle(self, x, y):
        best, best_key = -1, -1
        key, active = self.key, self.active
        for rid, (x1, y1, x2, y2) in enumerate(self.boxes):
            if active[rid] and key[rid] > best_key and x1 <= x <= x2 and y1 <= y <= y2:
                best, best_key = rid, key[rid]
        return best


def solve(operation_names, argument_lists):
    if operation_names[0] != 'RectangleBoard' or len(argument_lists[0]) != 2:
        raise ValueError('exact initial constructor required')
    instance = RectangleBoard(*argument_lists[0])
    allowed = ['addRectangle', 'getTopRectangle']
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        result.append(getattr(instance, name)(*arguments))
    return result
