class _Entry:
    def __init__(self, key=None, value=None):
        self.key = key
        self.value = value
        self.previous = None
        self.following = None


class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.entries = {}
        self.first = _Entry()
        self.last = _Entry()
        self.first.following = self.last
        self.last.previous = self.first

    def _remove(self, entry):
        entry.previous.following = entry.following
        entry.following.previous = entry.previous

    def _append(self, entry):
        entry.previous = self.last.previous
        entry.following = self.last
        self.last.previous.following = entry
        self.last.previous = entry

    def get(self, key):
        entry = self.entries.get(key)
        if entry is None:
            return -1
        self._remove(entry)
        self._append(entry)
        return entry.value

    def put(self, key, value):
        entry = self.entries.get(key)
        if entry is None:
            entry = _Entry(key, value)
            self.entries[key] = entry
        else:
            entry.value = value
            self._remove(entry)
        self._append(entry)
        if len(self.entries) > self.capacity:
            oldest = self.first.following
            self._remove(oldest)
            del self.entries[oldest.key]
