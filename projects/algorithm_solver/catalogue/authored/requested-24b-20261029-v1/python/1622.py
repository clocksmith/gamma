"""Original Fancy candidate. Independent qualification is pending."""

class Fancy:
    def __init__(self):
        self._values = []
        self._scale = 1
        self._offset = 0
        self._inverse_scale = 1

    def append(self, val):
        self._values.append((val - self._offset) * self._inverse_scale % 1000000007)

    def addAll(self, inc):
        self._offset = (self._offset + inc) % 1000000007

    def multAll(self, m):
        self._scale = self._scale * m % 1000000007
        self._offset = self._offset * m % 1000000007
        self._inverse_scale = self._inverse_scale * pow(m, 1000000005, 1000000007) % 1000000007

    def getIndex(self, idx):
        if idx >= len(self._values):
            return -1
        return (self._values[idx] * self._scale + self._offset) % 1000000007
