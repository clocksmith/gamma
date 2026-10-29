"""Original leaf-pair development candidate; qualification pending."""
def solve(root, distance):
    histograms = {}
    stack = [(root, False)]
    answer = 0
    while stack:
        node, ready = stack.pop()
        if node is None:
            continue
        if not ready:
            stack.append((node, True))
            stack.append((node.right, False))
            stack.append((node.left, False))
            continue
        counts = [0] * distance
        if node.left is None and node.right is None:
            counts[0] = 1
        else:
            left = histograms.pop(node.left, [0] * distance)
            right = histograms.pop(node.right, [0] * distance)
            for a, x in enumerate(left):
                for b, y in enumerate(right):
                    if a + b + 2 <= distance:
                        answer += x * y
            for depth in range(1, distance):
                counts[depth] = left[depth - 1] + right[depth - 1]
        histograms[node] = counts
    return answer

class Solution:
    def countPairs(self, root, distance):
        return solve(root, distance)
