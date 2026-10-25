class Solution:
    def minDominoRotations(self, tops, bottoms):
        def rotations(target):
            top_changes = 0
            bottom_changes = 0
            for top, bottom in zip(tops, bottoms):
                if top != target and bottom != target:
                    return len(tops) + 1
                if top != target:
                    top_changes += 1
                if bottom != target:
                    bottom_changes += 1
            return min(top_changes, bottom_changes)

        best = min(rotations(tops[0]), rotations(bottoms[0]))
        return best if best <= len(tops) else -1
