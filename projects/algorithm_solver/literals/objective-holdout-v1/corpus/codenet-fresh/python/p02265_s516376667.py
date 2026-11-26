from collections import deque
from sys import stdin
N = int(stdin.readline().rstrip())
d = deque()
for i in range(N):
    op_key = stdin.readline().rstrip().split()
    if op_key[0] == 'insert':
        d.appendleft(op_key[1])
    elif op_key[0] == 'delete':
        try:
            d.remove(op_key[1])
        except:
            pass
    elif op_key[0] == 'deleteFirst':
        d.popleft()
    elif op_key[0] == 'deleteLast':
        d.pop()
print(*d)
