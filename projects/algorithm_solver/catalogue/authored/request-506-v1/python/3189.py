# Original implementation. Contract: https://leetcode.com/problems/minimum-moves-to-get-a-peaceful-board/
def solve(rooks):return sum(abs(x-i) for i,x in enumerate(sorted(p[0] for p in rooks)))+sum(abs(y-i) for i,y in enumerate(sorted(p[1] for p in rooks)))
