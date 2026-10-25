class Solution:
    def confusingNumberII(self, limit):
        digits = [(0, 0), (1, 1), (6, 9), (8, 8), (9, 6)]
        pending = [(0, 0, 1)]
        total = 0
        while pending:
            number, rotated, place = pending.pop()
            if number != rotated:
                total += 1
            for digit, rotation in digits:
                successor = number * 10 + digit
                if successor > 0 and successor <= limit:
                    pending.append((successor, rotation * place + rotated, place * 10))
        return total
