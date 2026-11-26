N = int(input())
S = [input() for _ in range(N)]
Alist = [word for word in S if word[-1] == 'A']
Blist = [word for word in S if word[0] == 'B']
ABlist = [word for word in S if word[0] == 'B' and word[-1] == 'A']
Slist = [word.count('AB') for word in S]
C = min(len(Alist),len(Blist))
if len(Alist) == 0 and len(Blist) == 0:
    print(sum(Slist))
elif len(ABlist) == len(Alist) and len(ABlist) == len(Blist):
    print(sum(Slist)+len(ABlist)-1)
else:
    print(sum(Slist)+min(C,N-1))