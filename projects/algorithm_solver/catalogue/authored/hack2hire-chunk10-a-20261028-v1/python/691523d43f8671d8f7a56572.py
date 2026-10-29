"""Hack2Hire 691523d43f8671d8f7a56572 (Design Persistent Key-Value Store, variant 2 of 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


MAGIC = [80, 75, 86, 50]


def _u32(n):
    return [n >> 24 & 255, n >> 16 & 255, n >> 8 & 255, n & 255]


def _parse(body):
    """Return the entries of a level-1 body as a dict, or None when anything is malformed."""
    size = len(body)

    def word(i):
        return ((body[i] * 256 + body[i + 1]) * 256 + body[i + 2]) * 256 + body[i + 3] if i + 4 <= size else -1
    count = word(0)
    if count < 0:
        return None
    i, out, last = 4, {}, None
    for _ in range(count):
        n = word(i)
        if not 1 <= n <= 10 or i + 4 + n > size:
            return None
        key = ''.join(map(chr, body[i + 4:i + 4 + n]))
        i += 4 + n
        if not all('a' <= c <= 'z' or '0' <= c <= '9' for c in key) or (last is not None and key <= last):
            return None
        n = word(i)
        if not 1 <= n <= 20 or i + 4 + n > size:
            return None
        value = ''.join(map(chr, body[i + 4:i + 4 + n]))
        i += 4 + n
        if not all(' ' <= c <= '~' for c in value):
            return None
        out[key] = value
        last = key
    return out if i == size else None


class PersistentKVStore:
    def __init__(self):
        self.data = {}

    def set(self, key, value):
        self.data[key] = value

    def get(self, key):
        return self.data.get(key, '')

    def delete(self, key):
        return self.data.pop(key, None) is not None

    def save(self):
        body = _u32(len(self.data))
        for key in sorted(self.data):
            value = self.data[key]
            body += _u32(len(key))
            body += key.encode('ascii')
            body += _u32(len(value))
            body += value.encode('ascii')
        return MAGIC + body + _u32(sum(body) % 4294967296)

    def load(self, blob):
        if len(blob) < 12 or blob[:4] != MAGIC:
            return False
        body = blob[4:-4]
        tail = blob[-4:]
        if ((tail[0] * 256 + tail[1]) * 256 + tail[2]) * 256 + tail[3] != sum(body) % 4294967296:
            return False
        parsed = _parse(body)
        if parsed is None:
            return False
        self.data = parsed  # swap only after full validation
        return True


def solve(operation_names, argument_lists):
    if operation_names[0] != 'PersistentKVStore' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = PersistentKVStore(*argument_lists[0])
    allowed = {'set', 'get', 'delete', 'save', 'load'}
    voids = {'set'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
