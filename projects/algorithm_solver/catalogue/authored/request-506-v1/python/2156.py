# Original candidate implementation. Contract: https://leetcode.com/problems/find-substring-with-given-hash-value/
def solve(s,power,modulo,k,hashValue):
    outgoing=pow(power,k,modulo);value=0;answer=0
    for i in range(len(s)-1,-1,-1):
        value=(value*power+ord(s[i])-96)%modulo
        if i+k<len(s):value=(value-(ord(s[i+k])-96)*outgoing)%modulo
        if i+k<=len(s) and value==hashValue:answer=i
    return s[answer:answer+k]
