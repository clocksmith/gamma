S = input()
res = "Yes"
if S.count('N') and not S.count('S'):
    res = "No"
if not S.count('N') and S.count('S'):
    res = "No"
if S.count('E') and not S.count('W'):
    res = "No"
if not S.count('E') and S.count('W'):
    res = "No"
print(res)
