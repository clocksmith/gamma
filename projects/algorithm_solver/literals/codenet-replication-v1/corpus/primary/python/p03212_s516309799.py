N = int(input())
L = []


def f(v: str):
    for i in list('357'):
        new_v = v + i
        if N < int(new_v):
            continue
        if new_v.count('3') >= 1 and new_v.count('5') >= 1 and new_v.count(
                '7') >= 1:
            L.append(new_v)
        f(new_v)


f('')
# print(f'{L=}')
ans = len(L)
print(ans)
