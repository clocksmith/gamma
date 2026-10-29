"""Hack2Hire 67cf4b1faca6a2fa74a72cfd (Set Parity Bits) over an INFERRED spec; qualification unknown."""

def solve(byte):
    low = byte & 127
    x = low ^ (low >> 4)
    x ^= x >> 2
    x ^= x >> 1
    return low | ((x & 1) << 7)


class Solution:
    def setParityBit(self, byte):
        return solve(byte)
