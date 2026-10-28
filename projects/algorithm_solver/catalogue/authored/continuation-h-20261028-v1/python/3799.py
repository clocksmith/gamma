"""Original frontend 3799 development variant; qualification unknown."""

def solve(words):
    ordered = sorted(words)
    answer = []
    for top in ordered:
        for left in ordered:
            if left == top or top[0] != left[0]:
                continue
            for right in ordered:
                if right in (top, left) or top[3] != right[0]:
                    continue
                for bottom in ordered:
                    if bottom not in (top, left, right) and bottom[0] == left[3] and bottom[3] == right[3]:
                        answer.append([top, left, right, bottom])
    return answer


class Solution:
    def wordSquares(self, words):
        return solve(words)
