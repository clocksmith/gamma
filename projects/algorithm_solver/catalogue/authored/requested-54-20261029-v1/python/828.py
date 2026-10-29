"""Original development candidate; independent qualification pending."""
def solve(s):
    last = {}
    answer = 0
    for i, ch in enumerate(s):
        a,b = last.get(ch, (-1,-1))
        answer += (b-a)*(i-b)
        last[ch] = (b,i)
    return answer + sum((b-a)*(len(s)-b) for a,b in last.values())


class Solution:
    def uniqueLetterString(self, s):
        return solve(s)
