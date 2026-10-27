"""535. Encode and Decode TinyURL."""

class Codec:
    """Per-instance reversible URL mapping; no network access or global registry."""
    def __init__(self):
        self.forward = {}
        self.reverse = {}
        self.next_id = 0

    def encode(self, longUrl: str) -> str:
        if longUrl in self.forward:
            return self.forward[longUrl]
        alphabet = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        value = self.next_id
        self.next_id += 1
        digits = []
        while True:
            value, digit = divmod(value, 62)
            digits.append(alphabet[digit])
            if value == 0:
                break
        short = 'http://tinyurl.com/' + ''.join(reversed(digits))
        self.forward[longUrl] = short
        self.reverse[short] = longUrl
        return short

    def decode(self, shortUrl: str) -> str:
        return self.reverse[shortUrl]


def solve(operations: list[str], arguments: list[list]) -> list:
    """Replay native operations on one request-local instance."""
    if not operations:
        return []
    instance = Codec(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result


Solution = Codec
