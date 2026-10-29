"""Original development candidate; independent qualification pending."""
class FreqStack:
    def __init__(self):
        self.frequency = {}
        self.groups = {}
        self.maximum = 0

    def push(self, val):
        frequency = self.frequency.get(val,0)+1
        self.frequency[val] = frequency
        self.groups.setdefault(frequency,[]).append(val)
        self.maximum = max(self.maximum,frequency)

    def pop(self):
        value = self.groups[self.maximum].pop()
        self.frequency[value] -= 1
        if not self.groups[self.maximum]:
            self.maximum -= 1
        return value
