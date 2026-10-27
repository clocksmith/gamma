# Original candidate implementation. Contract: https://leetcode.com/problems/number-of-equal-count-substrings/
def solve(s,count):
    answer=0;values=[ord(c)-97 for c in s]
    for distinct in range(1,27):
        width=distinct*count
        if width>len(s):break
        frequencies=[0]*26;matched=0
        for i,c in enumerate(values):
            matched-=frequencies[c]==count;frequencies[c]+=1;matched+=frequencies[c]==count
            if i>=width:
                old=values[i-width];matched-=frequencies[old]==count;frequencies[old]-=1;matched+=frequencies[old]==count
            if i+1>=width and matched==distinct:answer+=1
    return answer
