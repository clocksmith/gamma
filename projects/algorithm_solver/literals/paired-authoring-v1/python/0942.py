class Solution:
    def diStringMatch(self, s: str) -> list[int]:
        lowest = 0
        highest = len(s)
        result = []
        for character in s:
            if character == "I":
                result.append(lowest)
                lowest += 1
            else:
                result.append(highest)
                highest -= 1
        result.append(lowest)
        return result
