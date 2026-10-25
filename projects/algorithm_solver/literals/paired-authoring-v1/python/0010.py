class Solution:
    def isMatch(self, s: str, p: str) -> bool:
        previous = [False] * (len(p) + 1)
        previous[0] = True
        for index in range(1, len(p) + 1):
            if p[index - 1] == "*":
                previous[index] = previous[index - 2]

        for character in s:
            current = [False] * (len(p) + 1)
            for index in range(1, len(p) + 1):
                symbol = p[index - 1]
                if symbol == "*":
                    repeated = p[index - 2]
                    matches = repeated == "." or repeated == character
                    current[index] = current[index - 2] or (matches and previous[index])
                else:
                    matches = symbol == "." or symbol == character
                    current[index] = matches and previous[index - 1]
            previous = current
        return previous[-1]
