"""Hack2Hire 6934e59f5f306485cc5f08be (Find Duplicate Files, variant 2: chunked streams). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown."""

BLOCK = 64


class _Stream:
    def __init__(self, chunks):
        self.chunks, self.index, self.offset = chunks, 0, 0

    def read(self, n):
        out = []
        while len(out) < n and self.index < len(self.chunks):
            chunk = self.chunks[self.index]
            take = min(n - len(out), len(chunk) - self.offset)
            out.extend(chunk[self.offset:self.offset + take])
            self.offset += take
            if self.offset == len(chunk):
                self.index += 1
                self.offset = 0
        return out


def solve(root):
    paths, streams, sizes, stack = [], [], [], [(root, '')]
    while stack:
        node, prefix = stack.pop()
        for f in node['files']:
            paths.append(prefix + '/' + f['name'])
            streams.append(_Stream(f['chunks']))
            sizes.append(sum(len(c) for c in f['chunks']))
        for d in node['directories']:
            stack.append((d, prefix + '/' + d['name']))
    by_size = {}
    for i, size in enumerate(sizes):
        by_size.setdefault(size, []).append(i)
    groups = []
    for size, members in by_size.items():
        work = [(members, 0)]
        while work:
            group, offset = work.pop()
            if len(group) < 2:
                continue
            if offset >= size:
                groups.append(sorted(paths[i] for i in group))
                continue
            split = {}
            for i in group:
                split.setdefault(tuple(streams[i].read(BLOCK)), []).append(i)
            for sub in split.values():
                work.append((sub, offset + BLOCK))
    groups.sort()
    return groups


class Solution:
    def findDuplicateFiles(self, root):
        return solve(root)
