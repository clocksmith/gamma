"""157. Read N Characters Given Read4."""
def solve(buf: list[str], n: int, read4_fn=None) -> int:
    if read4_fn is None:
        read4_fn = globals()['read4']
    written = 0
    temporary = [''] * 4
    while written < n:
        count = read4_fn(temporary)
        if count == 0:
            break
        for index in range(min(count, n - written)):
            buf[written] = temporary[index]
            written += 1
    return written

class Solution:
    def read(self, buf: list[str], n: int) -> int:
        return solve(buf, n)
