import fileinput

chr_master = [
    ' ', '\',.!?', 'abcABC', 'defDEF', 'ghiGHI',
    'jklJKL', 'mnoMNO', 'pqrsPQRS', 'tuvTUV', 'wxyzWXYZ'
]

for s in (line.strip() for line in fileinput.input()):
    s += '!'
    prev_c = None
    cnt = 0
    ans = ''
    for c in s:
        if c == prev_c:
            cnt += 1
            continue
        if prev_c == '0':
            if cnt > 1:
                ans += ' ' * (cnt - 1)
        else:
            if prev_c is not None:
                ans += chr_master[int(prev_c)][cnt - 1]

        prev_c = c
        cnt = 1
    print(ans)