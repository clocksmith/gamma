"""468. Validate IP Address. Check the explicit textual formats; do not accept compressed IPv6 or Unicode digits."""

def solve(queryIP: str) -> str:
    if '.' in queryIP:
        parts = queryIP.split('.')
        if len(parts) == 4 and all(part and len(part) <= 3
                and all('0' <= char <= '9' for char in part)
                and (len(part) == 1 or part[0] != '0') and int(part) <= 255 for part in parts):
            return 'IPv4'
    else:
        parts = queryIP.split(':')
        if len(parts) == 8 and all(1 <= len(part) <= 4
                and all(char in '0123456789abcdefABCDEF' for char in part) for part in parts):
            return 'IPv6'
    return 'Neither'


class Solution:
    def validIPAddress(self, queryIP: str) -> str:
        return solve(queryIP)
