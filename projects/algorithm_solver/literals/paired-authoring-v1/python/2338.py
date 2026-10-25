def multiply_mod(first: int, second: int, modulus: int) -> int:
    result = 0
    while second > 0:
        if second % 2 == 1:
            result = (result + first) % modulus
        first = (first + first) % modulus
        second //= 2
    return result


class Solution:
    def idealArrays(self, n: int, maxValue: int) -> int:
        modulus = 1000000007
        exponent_limit = 0
        power = 1
        while power * 2 <= maxValue:
            power *= 2
            exponent_limit += 1
        combinations = [1] * (exponent_limit + 1)
        for _ in range(1, n):
            for exponent in range(1, exponent_limit + 1):
                combinations[exponent] = (combinations[exponent] + combinations[exponent - 1]) % modulus
        smallest = list(range(maxValue + 1))
        prime = 2
        while prime * prime <= maxValue:
            if smallest[prime] == prime:
                for multiple in range(prime * prime, maxValue + 1, prime):
                    if smallest[multiple] == multiple:
                        smallest[multiple] = prime
            prime += 1
        answer = 0
        for value in range(1, maxValue + 1):
            remaining = value
            ways = 1
            while remaining > 1:
                prime = smallest[remaining]
                exponent = 0
                while remaining % prime == 0:
                    remaining //= prime
                    exponent += 1
                ways = multiply_mod(ways, combinations[exponent], modulus)
            answer = (answer + ways) % modulus
        return answer
