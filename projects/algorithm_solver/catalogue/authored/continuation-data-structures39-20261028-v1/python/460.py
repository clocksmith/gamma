"""Original frontend 460 variant; qualification unknown."""


class LFUCache:
    def __init__(self, capacity: int):
        self.cap = capacity
        self.min_freq = 0
        self.key_val_freq = {}
        self.freq_keys = {}

    def _touch(self, key: int, new_val=None) -> int:
        val, freq = self.key_val_freq[key]
        if new_val is not None:
            val = new_val
        bucket = self.freq_keys[freq]
        del bucket[key]
        if not bucket:
            del self.freq_keys[freq]
            if self.min_freq == freq:
                self.min_freq += 1
        nxt_freq = freq + 1
        self.freq_keys.setdefault(nxt_freq, {})[key] = True
        self.key_val_freq[key] = (val, nxt_freq)
        return val

    def get(self, key: int) -> int:
        if key not in self.key_val_freq:
            return -1
        return self._touch(key)

    def put(self, key: int, value: int) -> None:
        if self.cap <= 0:
            return
        if key in self.key_val_freq:
            self._touch(key, value)
            return
        if len(self.key_val_freq) == self.cap:
            min_bucket = self.freq_keys[self.min_freq]
            evict_key = next(iter(min_bucket))
            del min_bucket[evict_key]
            if not min_bucket:
                del self.freq_keys[self.min_freq]
            del self.key_val_freq[evict_key]
        self.key_val_freq[key] = (value, 1)
        self.freq_keys.setdefault(1, {})[key] = True
        self.min_freq = 1


def solve(operation_names, argument_lists):
    instance = LFUCache(argument_lists[0][0])
    out = [None]
    for op, args in zip(operation_names[1:], argument_lists[1:]):
        if op == "get":
            out.append(instance.get(args[0]))
        elif op == "put":
            instance.put(args[0], args[1])
            out.append(None)
        else:
            raise ValueError("unknown operation")
    return out
