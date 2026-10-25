"""1653. Minimum Deletions to Make String Balanced: delete the current a or every preceding b."""


def solve(s: str) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    deletions = b_count = 0
    for character in s:
        if character == "b":
            b_count += 1
        else:
            deletions = min(deletions + 1, b_count)
    return deletions


class Solution:
    def minimumDeletions(self, s: str) -> int:
        return solve(s)
