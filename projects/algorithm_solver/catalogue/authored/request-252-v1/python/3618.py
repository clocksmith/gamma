def solve(nums):
    n = len(nums)
    prime = bytearray(b'\x01') * n
    prime[0] = 0
    if n > 1:
        prime[1] = 0
    factor = 2
    while factor * factor < n:
        if prime[factor]:
            for multiple in range(factor * factor, n, factor):
                prime[multiple] = 0
        factor += 1
    return abs(sum(value if prime[i] else -value for i, value in enumerate(nums)))
