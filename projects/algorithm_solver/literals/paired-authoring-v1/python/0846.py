class Solution:
    def isNStraightHand(self, hand: list[int], groupSize: int) -> bool:
        if len(hand) % groupSize != 0:
            return False

        counts = {}
        for value in hand:
            counts[value] = counts.get(value, 0) + 1
        ordered = sorted(counts)
        for start in ordered:
            remaining = counts[start]
            if remaining == 0:
                continue
            for offset in range(groupSize):
                value = start + offset
                available = counts.get(value, 0)
                if available < remaining:
                    return False
                counts[value] = available - remaining
        return True
