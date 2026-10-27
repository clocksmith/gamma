# Original candidate implementation. Contract: https://leetcode.com/problems/make-string-anti-palindrome/
def solve(s):
    a=sorted(s);half=len(a)//2;counts=[s.count(chr(97+i)) for i in range(26)]
    if max(counts)>half:return '-1'
    left=a[:half];available=[0]*26;forbidden=[0]*26
    for ch in a[half:]:available[ord(ch)-97]+=1
    for ch in left:forbidden[ord(ch)-97]+=1
    right=[]
    for pos in range(half):
        ban=ord(left[half-pos-1])-97;forbidden[ban]-=1;remaining=half-pos-1
        forced=next((c for c in range(26) if available[c]>remaining-forbidden[c]),None)
        choice=forced if forced is not None else next(c for c in range(26) if c!=ban and available[c])
        if choice==ban:return '-1'
        available[choice]-=1;right.append(chr(97+choice))
    return ''.join(left+right)
