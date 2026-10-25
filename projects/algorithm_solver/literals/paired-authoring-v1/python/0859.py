class Solution:
    def buddyStrings(self, s: str, goal: str) -> bool:
        if len(s) != len(goal):
            return False
        if s == goal:
            return len(set(s)) < len(s)

        mismatches = []
        for index in range(len(s)):
            if s[index] != goal[index]:
                mismatches.append(index)
                if len(mismatches) > 2:
                    return False
        if len(mismatches) != 2:
            return False
        first, second = mismatches
        return s[first] == goal[second] and s[second] == goal[first]
