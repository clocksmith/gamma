"""165. Compare Version Numbers."""
def solve(version1: str, version2: str) -> int:
    left = list(map(int, version1.split('.')))
    right = list(map(int, version2.split('.')))
    size = max(len(left), len(right))
    left.extend([0] * (size - len(left)))
    right.extend([0] * (size - len(right)))
    return (left > right) - (left < right)

class Solution:
    def compareVersion(self, version1: str, version2: str) -> int:
        return solve(version1, version2)
