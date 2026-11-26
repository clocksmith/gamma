from collections import deque
while True:
    S = input()
    if S == ".":
        break
    que = deque()
    flag = True
    for s in S:
        if s == "(":
            que.append(1)
        elif s == "[":
            que.append(-1)
        elif s == ")" or s == "]":
            if len(que) <= 0:
                flag = False
                break
            temp1 = -1 if s == ")"else 1
            temp2 = que.pop()
            if temp1 + temp2 != 0:
                flag = False
                break
    if len(que) != 0:
        flag = False

    if flag:
        print("yes")
    else:
        print("no")
