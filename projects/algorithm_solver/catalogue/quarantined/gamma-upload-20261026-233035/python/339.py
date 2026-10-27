"""339. Nested List Weight Sum."""
def solve(nestedList) -> int:
    def visit(values, depth):
        total = 0
        for item in values:
            if item.isInteger():
                total += item.getInteger() * depth
            else:
                total += visit(item.getList(), depth + 1)
        return total
    return visit(nestedList, 1)

class Solution:
    def depthSum(self, nestedList) -> int:
        return solve(nestedList)
