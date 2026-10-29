"""Hack2Hire 6a0b74fac84b6e8a3be18c83 (Find IPv4 Addresses in Nested Files) over an INFERRED spec; qualification unknown."""


def _valid(run):
    parts = run.split('.')
    if len(parts) != 4:
        return False
    for part in parts:
        if not part or len(part) > 3 or (len(part) > 1 and part[0] == '0') or int(part) > 255:
            return False
    return True


def solve(root):
    found = set()
    stack = [root]
    while stack:
        node = stack.pop()
        for line in node['lines']:
            i, n = 0, len(line)
            while i < n:
                if line[i] == '.' or '0' <= line[i] <= '9':
                    j = i
                    while j < n and (line[j] == '.' or '0' <= line[j] <= '9'):
                        j += 1
                    run = line[i:j]
                    if _valid(run):
                        found.add(run)
                    i = j
                else:
                    i += 1
        stack.extend(node['children'])
    return sorted(found)


class Solution:
    def findIpAddresses(self, root):
        return solve(root)
