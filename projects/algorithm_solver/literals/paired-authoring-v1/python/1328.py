class Solution:
    def breakPalindrome(self, palindrome: str) -> str:
        if len(palindrome) <= 1:
            return ""
        for index in range(len(palindrome) // 2):
            if palindrome[index] != "a":
                return palindrome[:index] + "a" + palindrome[index + 1:]
        return palindrome[:-1] + "b"
