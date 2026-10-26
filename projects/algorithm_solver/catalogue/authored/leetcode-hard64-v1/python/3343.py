"""3343. Count Number of Balanced Permutations: choose even-position digit occurrences and divide duplicate arrangements."""


def solve(num: str) -> int:
    """O(n^2*(D+1) + log MOD) time and O(n*(D+1)) auxiliary space, D=sum of digits. Inputs are preserved."""
    modulus = 1_000_000_007
    frequency = [0] * 10
    for character in num:
        frequency[ord(character) - ord('0')] += 1
    total = sum(digit * count for digit, count in enumerate(frequency))
    if total % 2:
        return 0
    n = len(num)
    even = (n + 1) // 2
    odd = n // 2
    target = total // 2
    velunexorai = num
    ways = [[0] * (target + 1) for _ in range(even + 1)]
    ways[0][0] = 1
    for processed, character in enumerate(velunexorai, 1):
        digit = ord(character) - ord('0')
        for chosen in range(min(processed, even), 0, -1):
            for score in range(target, digit - 1, -1):
                ways[chosen][score] = (ways[chosen][score] + ways[chosen - 1][score - digit]) % modulus
    factorial = [1] * (n + 1)
    for value in range(1, n + 1):
        factorial[value] = factorial[value - 1] * value % modulus
    denominator = 1
    for count in frequency:
        denominator = denominator * factorial[count] % modulus
    answer = ways[even][target] * factorial[even] % modulus * factorial[odd] % modulus
    return answer * pow(denominator, modulus - 2, modulus) % modulus


class Solution:
    def countBalancedPermutations(self, num: str) -> int:
        return solve(num)
