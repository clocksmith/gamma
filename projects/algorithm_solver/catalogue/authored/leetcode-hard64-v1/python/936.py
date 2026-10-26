"""936. Stamping The Sequence: reverse erasure with mismatch dependency queues."""


def solve(stamp: str, target: str) -> list[int]:
    """O(n * m) time and space, n = target length, m = stamp length. Inputs are preserved."""
    width = len(stamp)
    length = len(target)
    if width > length:
        return []
    pending = [0] * (length - width + 1)
    waiting = [[] for _ in target]
    ready = []
    for start in range(len(pending)):
        for offset, character in enumerate(stamp):
            if target[start + offset] != character:
                pending[start] += 1
                waiting[start + offset].append(start)
        if pending[start] == 0:
            ready.append(start)
    erased = [False] * length
    removed = 0
    answer = []
    head = 0
    while head < len(ready):
        start = ready[head]
        head += 1
        answer.append(start)
        for index in range(start, start + width):
            if erased[index]:
                continue
            erased[index] = True
            removed += 1
            for window in waiting[index]:
                pending[window] -= 1
                if pending[window] == 0:
                    ready.append(window)
    return answer[::-1] if removed == length else []


class Solution:
    def movesToStamp(self, stamp: str, target: str) -> list[int]:
        return solve(stamp, target)
