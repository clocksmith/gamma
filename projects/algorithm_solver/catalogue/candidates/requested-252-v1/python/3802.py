"""3802. Number of Ways to Paint Sheets
Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
Signature: solve(n, limit).
Algorithm: For ordered colors with capped capacities a,b, count max(0,a+b-n+1); aggregate positive pairs with sorted suffix sums and remove self-pairs.
Complexity: O(m log m) time; O(m) space.
Numeric semantics: JavaScript BigInt and Python int accumulate exact pair counts; return a Number/int residue below 1000000007.
Mutation: Does not mutate input arrays, rows, strings, or trees.
Interface: Canonical solve(n, limit). Native judge method name was not supplied or verified.
Specification: https://leetcode.com/problems/number-of-ways-to-paint-sheets/description/
Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3802.Number%20of%20Ways%20to%20Paint%20Sheets/README_EN.md
Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
New readable implementations; no third-party source bodies copied verbatim.
No protected tests or private reference implementations used.
"""

from bisect import bisect_left


def solve(n, limit):
    caps = sorted(min(value, n - 1) for value in limit)
    prefix = [0]
    for cap in caps:
        prefix.append(prefix[-1] + cap)
    modulus = 1_000_000_007
    total = 0
    size = len(caps)
    for cap in caps:
        start = bisect_left(caps, n - cap)
        count = size - start
        contribution = prefix[size] - prefix[start] + count * (cap - n + 1)
        contribution -= max(0, 2 * cap - n + 1)
        total = (total + contribution) % modulus
    return total
