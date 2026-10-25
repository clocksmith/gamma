class Solution:
    def splitMessage(self, message: str, limit: int) -> list[str]:
        digit_total = 0
        parts = 0
        for candidate in range(1, len(message) + 1):
            digits = len(str(candidate))
            digit_total += digits
            if limit <= 2 * digits + 3:
                return []
            capacity = candidate * (limit - digits - 3) - digit_total
            if capacity >= len(message):
                parts = candidate
                break
        if parts == 0:
            return []
        output = []
        offset = 0
        for index in range(1, parts + 1):
            suffix = "<" + str(index) + "/" + str(parts) + ">"
            capacity = limit - len(suffix)
            output.append(message[offset:offset + capacity] + suffix)
            offset += capacity
        return output
