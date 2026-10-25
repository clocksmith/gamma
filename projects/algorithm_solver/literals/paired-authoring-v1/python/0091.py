class Solution:
    def numDecodings(self, s: str) -> int:
        if not s:
            return 0
        two_back = 1
        one_back = 0 if s[0] == "0" else 1
        for index in range(1, len(s)):
            current = 0 if s[index] == "0" else one_back
            if s[index - 1] == "1" or (
                s[index - 1] == "2" and s[index] <= "6"
            ):
                current += two_back
            # Shift only after both valid token lengths read their prefix counts.
            two_back = one_back
            one_back = current
        return one_back
