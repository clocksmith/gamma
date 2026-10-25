class Solution:
    def partitionLabels(self, s: str) -> list[int]:
        last = [-1] * 26
        for index, character in enumerate(s):
            last[ord(character) - 97] = index
        result = []
        start = 0
        end = 0
        for index, character in enumerate(s):
            end = max(end, last[ord(character) - 97])
            if index == end:
                result.append(index - start + 1)
                start = index + 1
        return result
