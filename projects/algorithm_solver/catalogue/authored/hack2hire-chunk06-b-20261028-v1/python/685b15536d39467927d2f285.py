"""Hack2Hire 685b15536d39467927d2f285 (Flatten HTML tags) over an INFERRED spec; qualification unknown."""

def solve(root):
    tokens = []
    stack = [(root, 0)]
    while stack:
        node, index = stack.pop()
        if index == 0:
            tokens.append('<' + node['tag'] + '>')
        children = node['children']
        if index < len(children):
            stack.append((node, index + 1))
            stack.append((children[index], 0))
        else:
            tokens.append('</' + node['tag'] + '>')
    return tokens


class Solution:
    def flattenHtml(self, root):
        return solve(root)
