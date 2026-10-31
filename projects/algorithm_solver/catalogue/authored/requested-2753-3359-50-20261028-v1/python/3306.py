"""Original frontend 3306 variant; qualification unknown."""


def solve(word: str, k: int) -> int:
    vowels = set("aeiou")

    def at_least(limit: int) -> int:
        vcnt = {}
        cons = 0
        left = 0
        ans = 0
        n = len(word)
        for right, ch in enumerate(word):
            if ch in vowels:
                vcnt[ch] = vcnt.get(ch, 0) + 1
            else:
                cons += 1
            while len(vcnt) == 5 and cons >= limit:
                ans += n - right
                lch = word[left]
                if lch in vowels:
                    vcnt[lch] -= 1
                    if vcnt[lch] == 0:
                        del vcnt[lch]
                else:
                    cons -= 1
                left += 1
        return ans

    return at_least(k) - at_least(k + 1)


countOfSubstrings = solve


class Solution:
    def countOfSubstrings(self, word: str, k: int) -> int:
        return solve(word, k)
