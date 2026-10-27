"""3984. Divisible Game.

Specification: https://leetcode.com/problems/divisible-game/description/
"""

from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(V log log V + n log V) time and O(V) space; prime divisors dominate composite choices, sparse Kadane updates. Inputs are preserved."""
    maximum = max(nums)
    smallest = [0] * (maximum + 1)
    for prime in range(2, maximum + 1):
        if smallest[prime]:
            continue
        smallest[prime] = prime
        if prime * prime <= maximum:
            for multiple in range(prime * prime, maximum + 1, prime):
                if smallest[multiple] == 0:
                    smallest[multiple] = prime
    state = {}
    prefix = 0
    best, chosen = -1, 2
    for value in nums:
        remaining = value
        while remaining > 1:
            prime = smallest[remaining]
            old = state.get(prime)
            ending = max(value, old[0] - (prefix - old[1]) + value) if old else value
            state[prime] = ending, prefix + value
            if ending > best or (ending == best and prime < chosen):
                best, chosen = ending, prime
            while remaining % prime == 0:
                remaining //= prime
        prefix += value
    return best * chosen % 1_000_000_007
