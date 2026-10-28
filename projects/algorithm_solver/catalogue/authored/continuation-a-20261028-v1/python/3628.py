def solve(s):
    remaining_t = s.count('T')
    left_l = lc = ct = existing = inserted_c = 0
    for character in s:
        inserted_c = max(inserted_c, left_l * remaining_t)
        if character == 'L':
            left_l += 1
        elif character == 'C':
            lc += left_l
            ct += remaining_t
        elif character == 'T':
            existing += lc
            remaining_t -= 1
    inserted_c = max(inserted_c, left_l * remaining_t)
    return existing + max(lc, ct, inserted_c)


class Solution:
    def numOfSubsequences(self, s):
        return solve(s)
