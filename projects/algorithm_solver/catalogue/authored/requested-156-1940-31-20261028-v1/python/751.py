"""Original frontend 751 variant; qualification unknown."""


def solve(ip: str, n: int):
    parts = [int(x) for x in ip.split(".")]
    cur = (parts[0] << 24) | (parts[1] << 16) | (parts[2] << 8) | parts[3]
    out = []
    while n > 0:
        step = cur & -cur if cur != 0 else (1 << 32)
        while step > n:
            step >>= 1
        tz = step.bit_length() - 1
        prefix = 32 - tz
        s_ip = f"{(cur >> 24) & 255}.{(cur >> 16) & 255}.{(cur >> 8) & 255}.{cur & 255}/{prefix}"
        out.append(s_ip)
        cur += step
        n -= step
    return out


ipToCIDR = solve


class Solution:
    def ipToCIDR(self, ip: str, n: int):
        return solve(ip, n)
