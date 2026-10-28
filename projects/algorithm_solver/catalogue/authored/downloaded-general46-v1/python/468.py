"""468. Validate IP Address (Medium).

Specification: https://leetcode.com/problems/validate-ip-address/description/
"""


def _is_ipv4(ip):
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    for part in parts:
        if len(part) == 0 or len(part) > 3:
            return False
        if len(part) > 1 and part[0] == '0':
            return False
        if not part.isdigit():
            return False
        if int(part) > 255:
            return False
    return True


def _is_ipv6(ip):
    parts = ip.split(':')
    if len(parts) != 8:
        return False
    for part in parts:
        if len(part) == 0 or len(part) > 4:
            return False
        for ch in part:
            lower = ch.lower()
            if not ((lower >= '0' and lower <= '9') or (lower >= 'a' and lower <= 'f')):
                return False
    return True


def solve(ip: str) -> str:
    if _is_ipv4(ip):
        return 'IPv4'
    if _is_ipv6(ip):
        return 'IPv6'
    return 'Neither'


class Solution:
    def validIPAddress(self, ip: str) -> str:
        return solve(ip)
