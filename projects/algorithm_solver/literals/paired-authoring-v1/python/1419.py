class Solution:
    def minNumberOfFrogs(self, croakOfFrogs: str) -> int:
        stages = {"c": 0, "r": 1, "o": 2, "a": 3, "k": 4}
        waiting = [0] * 4
        active = 0
        peak = 0
        for character in croakOfFrogs:
            stage = stages.get(character, -1)
            if stage == -1:
                return -1
            if stage == 0:
                waiting[0] += 1
                active += 1
                peak = max(peak, active)
            else:
                if waiting[stage - 1] == 0:
                    return -1
                waiting[stage - 1] -= 1
                if stage == 4:
                    active -= 1
                else:
                    waiting[stage] += 1
        return peak if active == 0 else -1
