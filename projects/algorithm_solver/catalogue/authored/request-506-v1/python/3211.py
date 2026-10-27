"""Original candidate for LeetCode 3211. Contract: https://leetcode.com/problems/generate-binary-strings-without-adjacent-zeros/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n*F(n)) output time and space; output lexical order, any order allowed"""
def solve(n):
    out=['']
    for _ in range(n):
        out=[s+c for s in out for c in ('0','1') if c=='1' or not s.endswith('0')]
    return out
