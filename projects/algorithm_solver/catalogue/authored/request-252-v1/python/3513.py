def solve(nums):
    n = len(nums)
    if n <= 2:
        return n
    # A permutation of 1..n spans every value below the next power of two.
    return 1 << n.bit_length()
