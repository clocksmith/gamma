def previous_visible(text: str, index: int) -> int:
    skipped = 0
    while index >= 0:
        if text[index] == "#":
            skipped += 1
        elif skipped > 0:
            skipped -= 1
        else:
            break
        index -= 1
    return index


class Solution:
    def backspaceCompare(self, s: str, t: str) -> bool:
        left = len(s) - 1
        right = len(t) - 1
        while left >= 0 or right >= 0:
            left = previous_visible(s, left)
            right = previous_visible(t, right)
            if left < 0 or right < 0:
                return left == right
            if s[left] != t[right]:
                return False
            left -= 1
            right -= 1
        return True
