class Solution:
    def optimalDivision(self, nums: list[int]) -> str:
        terms = []
        for value in nums:
            terms.append(str(value))
        if len(terms) == 1:
            return terms[0]
        if len(terms) == 2:
            return terms[0] + "/" + terms[1]
        return terms[0] + "/(" + "/".join(terms[1:]) + ")"
