class Solution:
    def countBinarySubstrings(self, s: str) -> int:
        if not s:
            return 0

        previous_run = 0
        current_run = 1
        count = 0
        for index in range(1, len(s)):
            if s[index] == s[index - 1]:
                current_run += 1
            else:
                count += min(previous_run, current_run)
                previous_run = current_run
                current_run = 1
        return count + min(previous_run, current_run)
