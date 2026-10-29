"""Hack2Hire 6934db665f306485cc5f08ba (Find Duplicate Files, variant 1). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown."""


def solve(root):
    files, stack = [], [(root, '')]
    while stack:
        node, prefix = stack.pop()
        for f in node['files']:
            files.append((prefix + '/' + f['name'], f['content']))
        for d in node['directories']:
            stack.append((d, prefix + '/' + d['name']))
    by_size = {}
    for path, content in files:
        by_size.setdefault(len(content), []).append((path, content))
    groups = []
    for bucket in by_size.values():
        if len(bucket) < 2:
            continue
        by_content = {}
        for path, content in bucket:
            by_content.setdefault(tuple(content), []).append(path)
        groups.extend(sorted(g) for g in by_content.values() if len(g) > 1)
    groups.sort()
    return groups


class Solution:
    def findDuplicateFiles(self, root):
        return solve(root)
