# Original candidate implementation. Contract: https://leetcode.com/problems/smallest-greater-multiple-made-of-two-digits/
def solve(k,digit1,digit2):
    digits=sorted({digit1,digit2});queue=[d for d in digits if d];head=0
    while head<len(queue):
        value=queue[head];head+=1
        if value>k and value%k==0:return value
        for d in digits:
            nxt=value*10+d
            if nxt<=2147483647:queue.append(nxt)
    return -1
