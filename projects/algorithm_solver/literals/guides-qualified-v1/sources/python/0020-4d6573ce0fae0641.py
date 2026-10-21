class Solution:

    def isValid(self, a):
        b = []
        c = {'()', '[]', '{}'}
        for d in a:
            if d in '({[':
                b.append(d)
            elif not b or b.pop() + d not in c:
                return False
        return not b
