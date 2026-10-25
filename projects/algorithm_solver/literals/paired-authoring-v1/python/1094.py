class Solution:
    def carPooling(self, trips: list[list[int]], capacity: int) -> bool:
        changes = {}
        for passengers, start, end in trips:
            changes[start] = changes.get(start, 0) + passengers
            changes[end] = changes.get(end, 0) - passengers
        onboard = 0
        for position in sorted(changes):
            onboard += changes[position]
            if onboard > capacity:
                return False
        return True
