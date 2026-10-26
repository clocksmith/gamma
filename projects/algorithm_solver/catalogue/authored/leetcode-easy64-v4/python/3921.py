"""3921. Score Validator (Easy).

Specification: https://leetcode.com/problems/score-validator/description/
"""


def solve(events: list[str]) -> list[int]:
    """O(n) time, O(1) space; stop immediately after the tenth wicket and preserve events."""
    score = 0
    wickets = 0
    for event in events:
        if event == 'W':
            wickets += 1
            if wickets == 10:
                break
        elif event == 'WD' or event == 'NB':
            score += 1
        else:
            score += int(event)
    return [score, wickets]


class Solution:
    def scoreValidator(self, events: list[str]) -> list[int]:
        return solve(events)
