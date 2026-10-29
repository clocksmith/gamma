"""Hack2Hire 6782bd403cd890ccd3798fc3 (Construct Restaurant Daily Menu) over an INFERRED spec; qualification unknown."""


def solve(menu):
    if not menu['active']:
        return None
    root = {'key': menu['key'], 'value': menu['value'], 'active': True, 'children': []}
    stack = [(menu, root)]
    while stack:
        source, copy = stack.pop()
        for child in source['children']:
            if child['active']:
                node = {'key': child['key'], 'value': child['value'], 'active': True, 'children': []}
                copy['children'].append(node)
                stack.append((child, node))
    return root


class Solution:
    def buildDailyMenu(self, menu):
        return solve(menu)
