"""306. Additive Number."""
def solve(num: str) -> bool:
    size = len(num)
    for first_end in range(1, size):
        if num[0] == '0' and first_end > 1:
            break
        first = int(num[:first_end])
        for second_end in range(first_end + 1, size):
            if num[first_end] == '0' and second_end - first_end > 1:
                break
            left, right = first, int(num[first_end:second_end])
            index = second_end
            while index < size:
                text = str(left + right)
                if not num.startswith(text, index):
                    break
                index += len(text)
                left, right = right, left + right
            if index == size:
                return True
    return False

class Solution:
    def isAdditiveNumber(self, num: str) -> bool:
        return solve(num)
