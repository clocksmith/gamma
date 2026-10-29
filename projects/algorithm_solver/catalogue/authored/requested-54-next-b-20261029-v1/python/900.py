"""Original run iterator development candidate; qualification unknown."""
class RLEIterator:
    def __init__(self, encoding):
        self.encoding = list(encoding)
        self.index = 0
        self.used = 0

    def next(self, n):
        while self.index < len(self.encoding):
            remaining = self.encoding[self.index]-self.used
            if n <= remaining:
                self.used += n
                return self.encoding[self.index+1]
            n -= remaining
            self.index += 2
            self.used = 0
        return -1
