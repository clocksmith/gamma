class Solution:
    def shortestPalindrome(self, s):
        text = s + '#' + s[::-1]
        prefix = [0] * len(text)
        for i in range(1, len(text)):
            j = prefix[i - 1]
            while j and text[i] != text[j]:
                j = prefix[j - 1]
            if text[i] == text[j]:
                j += 1
            prefix[i] = j
        return s[prefix[-1]:][::-1] + s
