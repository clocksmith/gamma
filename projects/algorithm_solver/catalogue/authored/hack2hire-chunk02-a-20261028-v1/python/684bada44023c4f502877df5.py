"""Hack2Hire 684bada44023c4f502877df5 (IP CIDR Firewall); INFERRED spec (default deny); qualification unknown."""


def _to_int(ip):
    value = 0
    for part in ip.split('.'): value = value << 8 | int(part)
    return value


class IpFirewall:
    def __init__(self, rules):
        self.rules = []
        for action, target in rules:
            base, _, length = target.partition('/')
            bits = int(length) if length else 32
            mask = (0xFFFFFFFF << (32 - bits)) & 0xFFFFFFFF
            self.rules.append((mask, _to_int(base) & mask, action == 'ALLOW'))

    def isAllowed(self, ip):
        value = _to_int(ip)
        for mask, base, allow in self.rules:
            if value & mask == base: return allow
        return False


def solve(operations, arguments):
    firewall = IpFirewall(*arguments[0])
    return [None] + [getattr(firewall, op)(*row) for op, row in zip(operations[1:], arguments[1:])]
