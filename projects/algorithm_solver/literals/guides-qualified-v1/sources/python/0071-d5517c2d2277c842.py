class Solution:

    def simplifyPath(self, a):
        b = []
        for c in a.split('/'):
            if not c or c == '.':
                continue
            if c == '..':
                if b:
                    b.pop()
            else:
                b.append(c)
        return '/' + '/'.join(b)
