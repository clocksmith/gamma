class Solution:
    def letterCombinations(self, digits):
        mapping = ('abc', 'def', 'ghi', 'jkl', 'mno', 'pqrs', 'tuv', 'wxyz')
        result = ['']
        for digit in digits:
            result = [prefix + c for prefix in result for c in mapping[int(digit) - 2]]
        return result
