"""271. Encode and Decode Strings."""
class Codec:
    def encode(self, strs: list[str]) -> str:
        return ''.join(f'{len(value)}#{value}' for value in strs)

    def decode(self, s: str) -> list[str]:
        result = []
        index = 0
        while index < len(s):
            separator = s.index('#', index)
            length = int(s[index:separator])
            start = separator + 1
            result.append(s[start:start + length])
            index = start + length
        return result

def solve(strs: list[str]) -> list[str]:
    codec = Codec()
    return codec.decode(codec.encode(strs))
