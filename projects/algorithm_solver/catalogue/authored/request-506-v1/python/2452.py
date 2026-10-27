# Original candidate implementation. Contract: https://leetcode.com/problems/words-within-two-edits-of-dictionary/
def solve(queries, dictionary):
    return [word for word in queries if any(sum(a != b for a,b in zip(word,other)) <= 2 for other in dictionary)]
