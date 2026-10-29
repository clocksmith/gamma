"""Original frontend 535 variant; qualification unknown."""


_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _to_base62(num: int) -> str:
    if num == 0:
        return "0"
    chars = []
    while num > 0:
        chars.append(_ALPHABET[num % 62])
        num //= 62
    return "".join(reversed(chars))


class Codec:
    def __init__(self):
        self.url_to_code = {}
        self.code_to_url = {}
        self.counter = 1

    def encode(self, longUrl: str) -> str:
        if longUrl in self.url_to_code:
            code = self.url_to_code[longUrl]
        else:
            code = _to_base62(self.counter)
            self.counter += 1
            self.url_to_code[longUrl] = code
            self.code_to_url[code] = longUrl
        return "http://tinyurl.com/" + code

    def decode(self, shortUrl: str) -> str:
        code = shortUrl.rsplit("/", 1)[-1]
        return self.code_to_url[code]


def solve(url: str) -> str:
    codec = Codec()
    return codec.decode(codec.encode(url))
