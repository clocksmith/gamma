# Original candidate implementation. Contract: https://leetcode.com/problems/minimum-costs-using-the-train-line/
def solve(regular,express,expressCost):
    r=0;e=expressCost;out=[]
    for a,b in zip(regular,express):
        r,e=min(r,e)+a,min(e,r+expressCost)+b
        out.append(min(r,e))
    return out
