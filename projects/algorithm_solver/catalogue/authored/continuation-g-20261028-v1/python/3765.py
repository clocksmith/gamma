def solve(num):
    def prime(x):
        if x < 2:
            return False
        if x % 2 == 0:
            return x == 2
        d = 3
        while d * d <= x:
            if x % d == 0:
                return False
            d += 2
        return True
    text = str(num)
    for i in range(1, len(text) + 1):
        if not prime(int(text[:i])) or not prime(int(text[-i:])):
            return False
    return True


class Solution:
    def completePrime(self, num):
        return solve(num)
