class Solution:
    def confusingNumberII(self, limit: int) -> int:
        if limit <= 0:
            return 0
        digits = [0, 1, 6, 8, 9]
        rotations = [0, 1, 9, 8, 6]
        bound = str(limit)
        total = sum(4 * 5 ** (length - 1) for length in range(1, len(bound)))
        for index, character in enumerate(bound):
            digit = int(character)
            allowed = digits[1:] if index == 0 else digits
            total += sum(value < digit for value in allowed) * 5 ** (len(bound) - index - 1)
            if digit not in allowed:
                break
        else:
            total += 1
        unchanged = 0
        def visit(buffer, left, right):
            nonlocal unchanged
            if left > right:
                value = int("".join(buffer))
                if 0 < value <= limit:
                    unchanged += 1
                return
            for digit, rotation in zip(digits, rotations):
                if left == 0 and len(buffer) > 1 and digit == 0:
                    continue
                if left == right and digit != rotation:
                    continue
                buffer[left] = str(digit)
                buffer[right] = str(rotation)
                visit(buffer, left + 1, right - 1)
        for length in range(1, len(bound) + 1):
            visit([""] * length, 0, length - 1)
        return total - unchanged
