"""364. Nested List Weight Sum II."""
def solve(nestedList) -> int:
    unweighted = weighted = 0
    level = nestedList
    while level:
        following = []
        for item in level:
            if item.isInteger():
                unweighted += item.getInteger()
            else:
                following.extend(item.getList())
        weighted += unweighted
        level = following
    return weighted

class Solution:
    def depthSumInverse(self, nestedList) -> int:
        return solve(nestedList)
