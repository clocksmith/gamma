# Original implementation. Contract: https://leetcode.com/problems/lexicographically-minimum-string-after-removing-stars/
def solve(s):
    positions=[[] for _ in range(26)];removed=set()
    for i,c in enumerate(s):
        if c=='*':
            for stack in positions:
                if stack:removed.add(stack.pop());break
        else:positions[ord(c)-97].append(i)
    return ''.join(c for i,c in enumerate(s) if c!='*' and i not in removed)
