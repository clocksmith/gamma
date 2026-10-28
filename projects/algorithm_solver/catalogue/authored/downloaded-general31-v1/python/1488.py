"""1488. Avoid Flood in The City (Medium).

Specification: https://leetcode.com/problems/avoid-flood-in-the-city/description/
"""


def solve(rains: list[int]) -> list[int]:
    answer = [1] * len(rains)
    last_rain = {}
    dry_days = []
    for day, lake in enumerate(rains):
        if lake == 0:
            dry_days.append(day)
            continue
        answer[day] = -1
        if lake in last_rain:
            previous = last_rain[lake]
            chosen = None
            for i, dry in enumerate(dry_days):
                if dry > previous:
                    chosen = i
                    break
            if chosen is None:
                return []
            answer[dry_days[chosen]] = lake
            dry_days.pop(chosen)
        last_rain[lake] = day
    return answer


class Solution:
    def avoidFlood(self, rains: list[int]) -> list[int]:
        return solve(rains)
