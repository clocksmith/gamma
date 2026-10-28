"""811. Subdomain Visit Count (Medium).

Specification: https://leetcode.com/problems/subdomain-visit-count/description/
"""


def solve(cpdomains: list[str]) -> list[str]:
    counts = {}
    for entry in cpdomains:
        space = entry.index(' ')
        count = int(entry[:space])
        domain = entry[space + 1:]
        parts = domain.split('.')
        for i in range(len(parts)):
            subdomain = ".".join(parts[i:])
            counts[subdomain] = counts.get(subdomain, 0) + count
    return sorted(f"{count} {domain}" for domain, count in counts.items())


class Solution:
    def subdomainVisits(self, cpdomains: list[str]) -> list[str]:
        return solve(cpdomains)
