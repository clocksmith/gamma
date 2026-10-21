class Solution:

    def isValidSudoku(self, a):
        b = [[False] * 9 for g in range(9)]
        c = [[False] * 9 for g in range(9)]
        d = [[False] * 9 for g in range(9)]
        for e in range(9):
            for f in range(9):
                h = a[e][f]
                if h == '.':
                    continue
                i = int(h) - 1
                j = e // 3 * 3 + f // 3
                if b[e][i] or c[f][i] or d[j][i]:
                    return False
                b[e][i] = True
                c[f][i] = True
                d[j][i] = True
        return True
