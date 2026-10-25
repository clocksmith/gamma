class Solution:
    def confusingNumber(self, number):
        rotation = {"0": "0", "1": "1", "6": "9", "8": "8", "9": "6"}
        original = str(number)
        digits = []
        for digit in reversed(original):
            if digit not in rotation:
                return False
            digits.append(rotation[digit])
        rotated = "".join(digits).lstrip("0") or "0"
        return rotated != original
