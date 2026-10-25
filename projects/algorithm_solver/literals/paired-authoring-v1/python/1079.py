class Solution:
    def numTilePossibilities(self, tiles: str) -> int:
        counts = [0] * 26
        for letter in tiles:
            counts[ord(letter) - 65] += 1
        ways = [1]
        for count in counts:
            if count == 0:
                continue
            following = [0] * (len(ways) + count)
            for length, existing in enumerate(ways):
                combinations = 1
                for used in range(count + 1):
                    if used > 0:
                        combinations = combinations * (length + used) // used
                    following[length + used] += existing * combinations
            ways = following
        return sum(ways) - 1
