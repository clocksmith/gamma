"""Hack2Hire 692f515ecd79766b0b310123 (Concurrent Web Crawler) over an INFERRED deterministic spec; qualification unknown."""
from collections import deque


def _hostname(url):
    rest = url[len('http://'):]
    slash = rest.find('/')
    return rest if slash < 0 else rest[:slash]


def solve(startUrl, links):
    host = _hostname(startUrl)
    seen = {startUrl}
    pending = deque([startUrl])
    while pending:
        url = pending.popleft()
        for found in links.get(url, ()):
            if found not in seen and _hostname(found) == host:
                seen.add(found)
                pending.append(found)
    return sorted(seen)


class Solution:
    def crawl(self, startUrl, links):
        return solve(startUrl, links)
