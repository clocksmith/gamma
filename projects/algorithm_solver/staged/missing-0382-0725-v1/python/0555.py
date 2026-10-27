"""555. Split Concatenated Strings. Choose the best orientation outside the cut string and enumerate its orientation and cut."""

def solve(strs: list[str]) -> str:
    best_parts = [max(text, text[::-1]) for text in strs]
    answer = ''
    for index, original in enumerate(strs):
        middle = ''.join(best_parts[index + 1:] + best_parts[:index])
        for text in (original, original[::-1]):
            for cut in range(len(text)):
                candidate = text[cut:] + middle + text[:cut]
                if candidate > answer:
                    answer = candidate
    return answer


class Solution:
    def splitLoopedString(self, strs: list[str]) -> str:
        return solve(strs)
