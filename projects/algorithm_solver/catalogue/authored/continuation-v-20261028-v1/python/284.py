class PeekingIterator:
    def __init__(self, iterator):
        self.iterator = iterator
        self.buffered = False
        self.value = None

    def peek(self):
        if not self.buffered:
            self.value = self.iterator.next()
            self.buffered = True
        return self.value

    def next(self):
        if self.buffered:
            self.buffered = False
            return self.value
        return self.iterator.next()

    def hasNext(self):
        return self.buffered or self.iterator.hasNext()
