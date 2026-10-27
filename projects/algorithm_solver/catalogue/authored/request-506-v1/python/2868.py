# Original implementation. Contract: https://leetcode.com/problems/the-wording-game/
def solve(a,b):
    words=sorted([(w,0) for w in a]+[(w,1) for w in b],reverse=True);winning=[[False]*27 for _ in range(2)];answer=False
    for word,owner in words:
        c=ord(word[0])-97;wins=not(winning[1-owner][c] or winning[1-owner][c+1])
        winning[owner][c]|=wins
        if owner==0 and word==a[0]:answer=wins
    return answer
