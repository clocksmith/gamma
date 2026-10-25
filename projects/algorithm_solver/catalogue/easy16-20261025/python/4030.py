def solve(s: str) -> bool:
    """Compare mirrored bits without constructing the bit string. O(n) time, O(1) space."""
    bit_count = 8 * len(s)
    for left in range(bit_count // 2):
        right = bit_count - left - 1
        left_bit = (ord(s[left // 8]) >> (7 - left % 8)) & 1
        right_bit = (ord(s[right // 8]) >> (7 - right % 8)) & 1
        if left_bit != right_bit:
            return False
    return True
