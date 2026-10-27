"""683. K Empty Slots. Linear scan of activation-day windows; interior bulbs must all activate later."""

def solve(bulbs: list[int], k: int) -> int:
    n = len(bulbs)
    days = [0] * n
    for day, position in enumerate(bulbs, 1):
        days[position - 1] = day
    left, right = 0, k + 1
    index = 1
    answer = n + 1
    while right < n:
        if index == right:
            answer = min(answer, max(days[left], days[right]))
            left = right
            right = left + k + 1
            index = left + 1
        elif days[index] < days[left] or days[index] < days[right]:
            left = index
            right = left + k + 1
            index = left + 1
        else:
            index += 1
    return answer if answer <= n else -1


class Solution:
    def kEmptySlots(self, bulbs: list[int], k: int) -> int:
        return solve(bulbs, k)
