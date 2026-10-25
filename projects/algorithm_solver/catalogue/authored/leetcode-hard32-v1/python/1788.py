"""1788. Maximize the Beauty of the Garden."""

def solve(flowers: list[int]) -> int:
    """O(n) expected time and space; equal endpoints enclose every positive interior value."""
    prefix = 0
    after_first = {}
    answer = 2 * min(flowers)
    for value in flowers:
        if value in after_first:
            candidate = 2 * value + prefix - after_first[value]
            answer = max(answer, candidate)
        prefix += max(value, 0)
        if value not in after_first:
            after_first[value] = prefix
    # The stated domain guarantees a repeated endpoint value and hence a valid garden.
    return answer


class Solution:
    def maximumBeauty(self, flowers: list[int]) -> int:
        return solve(flowers)
