"""Hack2Hire 687eda22cdb08328ca5a8483 (IP Routing Lookup) over an INFERRED spec; qualification unknown."""


def _address(text):
    a, b, c, d = text.split('.')
    return ((int(a) * 256 + int(b)) * 256 + int(c)) * 256 + int(d)


def solve(routes, queries):
    tables = {}  # prefix length -> {masked network: next hop}; later routes overwrite
    for prefix, hop in routes:
        base, length = prefix.split('/')
        length = int(length)
        tables.setdefault(length, {})[_address(base) >> (32 - length)] = hop
    lengths = sorted(tables, reverse=True)
    out = []
    for query in queries:
        ip = _address(query)
        answer = ''
        for length in lengths:
            hop = tables[length].get(ip >> (32 - length))
            if hop is not None:
                answer = hop
                break
        out.append(answer)
    return out


class Solution:
    def routeLookup(self, routes, queries):
        return solve(routes, queries)
