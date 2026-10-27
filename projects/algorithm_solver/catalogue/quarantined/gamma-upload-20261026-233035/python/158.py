"""158. Read N Characters Given Read4 II - Call Multiple Times."""
class Solution:
    def __init__(self):
        self.buffer = [''] * 4
        self.start = 0
        self.end = 0

    def read(self, buf: list[str], n: int) -> int:
        written = 0
        read4_fn = globals()['read4']
        while written < n:
            if self.start == self.end:
                self.end = read4_fn(self.buffer)
                self.start = 0
                if self.end == 0:
                    break
            while written < n and self.start < self.end:
                buf[written] = self.buffer[self.start]
                written += 1
                self.start += 1
        return written

def solve(read4_fn, requests: list[int]) -> list[str]:
    reader = Solution()
    old = globals().get('read4')
    globals()['read4'] = read4_fn
    try:
        result = []
        for n in requests:
            buf = [''] * n
            count = reader.read(buf, n)
            result.append(''.join(buf[:count]))
        return result
    finally:
        if old is None:
            globals().pop('read4', None)
        else:
            globals()['read4'] = old
