ai,ao,at,aj,al,aS,az=map(int,input().split())
ans = ao
if aj > 0 and al > 0 and ai > 0:
    print(ao + max(2 * (ai // 2 + al // 2 + aj // 2), 3 + 2 * ((ai - 1) // 2 + (al - 1) // 2 + (aj - 1) // 2)))
else:
    print(ao + 2 * (ai // 2 + al // 2 + aj // 2))
