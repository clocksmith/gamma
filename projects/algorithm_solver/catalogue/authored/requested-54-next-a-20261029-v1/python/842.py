"""Original development candidate; qualification unknown."""
def solve(num):
    limit = 2**31
    n = len(num)
    for i in range(1,min(10,n-2)+1):
        if i > 1 and num[0] == '0':
            break
        a = int(num[:i])
        if a >= limit:
            break
        for j in range(i+1,min(i+10,n-1)+1):
            if j-i > 1 and num[i] == '0':
                break
            b = int(num[i:j])
            if b >= limit:
                break
            sequence = [a,b]
            position = j
            while position < n:
                value = sequence[-2]+sequence[-1]
                text = str(value)
                if value >= limit or not num.startswith(text,position):
                    break
                sequence.append(value)
                position += len(text)
            if position == n and len(sequence) >= 3:
                return sequence
    return []


class Solution:
    def splitIntoFibonacci(self, num):
        return solve(num)
