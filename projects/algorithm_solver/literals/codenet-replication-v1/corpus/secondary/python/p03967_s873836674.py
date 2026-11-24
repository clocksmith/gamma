S = input()

e,o = [],[]
for i in range(len(S)):
    if i%2 == 0: e.append(S[i])
    else: o.append(S[i])

win,lose = 0,0
for s in e:
    if s == 'p': lose+=1
for s in o:
    if s == 'g': win+=1

print(win-lose)
