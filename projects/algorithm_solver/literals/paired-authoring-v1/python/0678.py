class Solution:
    def checkValidString(self, s: str) -> bool:
        minimum = 0
        maximum = 0
        for character in s:
            if character == "(":
                minimum += 1
                maximum += 1
            elif character == ")":
                minimum = max(0, minimum - 1)
                maximum -= 1
            else:
                minimum = max(0, minimum - 1)
                maximum += 1
            if maximum < 0:
                return False
        return minimum == 0
