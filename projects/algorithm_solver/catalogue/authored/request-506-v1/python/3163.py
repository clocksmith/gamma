# Original candidate implementation. Contract: https://leetcode.com/problems/string-compression-iii/
def solve(word):
    result=[];i=0
    while i<len(word):
        j=i+1
        while j<len(word) and j-i<9 and word[j]==word[i]: j+=1
        result.append(str(j-i)+word[i]);i=j
    return ''.join(result)
