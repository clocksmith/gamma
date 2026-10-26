"""1307. Verbal Arithmetic Puzzle: column-wise carry backtracking over at most ten letters; exponential search, no input mutation."""


def solve(words: list[str], result: str) -> bool:
    if any(len(word) > len(result) for word in words):
        return False
    letters = set(''.join(words) + result)
    if len(letters) > 10:
        return False
    leading = {word[0] for word in [*words, result] if len(word) > 1}
    assigned = {}
    used = [False] * 10

    def search(column: int, row: int, total: int) -> bool:
        if column == len(result):
            return total == 0
        if row < len(words):
            word = words[row]
            if column >= len(word):
                return search(column, row + 1, total)
            letter = word[-column - 1]
            if letter in assigned:
                return search(column, row + 1, total + assigned[letter])
            for digit in range(10):
                if used[digit] or (digit == 0 and letter in leading):
                    continue
                assigned[letter] = digit
                used[digit] = True
                valid = search(column, row + 1, total + digit)
                used[digit] = False
                del assigned[letter]
                if valid:
                    return True
            return False
        letter = result[-column - 1]
        digit, carry = total % 10, total // 10
        if letter in assigned:
            return assigned[letter] == digit and search(column + 1, 0, carry)
        if used[digit] or (digit == 0 and letter in leading):
            return False
        assigned[letter] = digit
        used[digit] = True
        valid = search(column + 1, 0, carry)
        used[digit] = False
        del assigned[letter]
        return valid

    return search(0, 0, 0)


class Solution:
    def isSolvable(self, words: list[str], result: str) -> bool:
        return solve(words, result)
