"""3401. Find Circular Gift Exchange Chains

Authored candidate. Not executed, syntax-checked, tested, or qualified.
Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
Signature: solve(secretSanta).
O(exchanges + cycles log cycles) time; O(exchanges) space.
A qualifying member has exactly one incoming and outgoing exchange in the supplied table. Self-gifts are not exchanges with another employee. Distinct (length,total) combinations are emitted once. chain_id is a 1-based ordinal after required sorting; its precise native convention needs coordinator confirmation.
Specification: https://leetcode.com/problems/find-circular-gift-exchange-chains/description/
Consulted reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3400-3499/3401.Find%20Circular%20Gift%20Exchange%20Chains/README_EN.md
"""

import re

def checked_integer(value):
    if not -9007199254740991 <= value <= 9007199254740991:
        raise OverflowError("Integer result exceeds the mock JSON safe-integer domain.")
    return value

def validate_rows(rows, schema, primary_key):
    if not isinstance(rows, list):
        raise TypeError("Expected a table as a list of row dictionaries.")
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise TypeError("Expected a row dictionary.")
        for column, declared in schema.items():
            if column not in row:
                raise TypeError("Missing column: " + column)
            value = row[column]
            if value is None and declared.endswith("?"):
                continue
            kind = declared.rstrip("?")
            valid = False
            if kind == "int":
                valid = type(value) is int and -9007199254740991 <= value <= 9007199254740991
            elif kind == "str":
                valid = isinstance(value, str) and not any(0xD800 <= ord(c) <= 0xDFFF for c in value)
            if not valid:
                raise TypeError("Invalid value for column: " + column)
        key = tuple(row[column] for column in primary_key)
        if key in seen:
            raise ValueError("Duplicate primary key.")
        seen.add(key)

def solve(secretSanta):
    validate_rows(secretSanta, {'giver_id': 'int', 'receiver_id': 'int', 'gift_value': 'int'}, ['giver_id', 'receiver_id'])
    outgoing = {}
    incoming_count = {}
    for gift in secretSanta:
        outgoing.setdefault(gift["giver_id"], []).append(gift)
        receiver = gift["receiver_id"]
        incoming_count[receiver] = incoming_count.get(receiver, 0) + 1

    def eligible(employee):
        return len(outgoing.get(employee, [])) == 1 and incoming_count.get(employee, 0) == 1

    visited = set()
    combinations = set()
    for start in outgoing:
        if not eligible(start) or start in visited:
            continue
        path = []
        position = {}
        current = start
        while eligible(current) and current not in visited and current not in position:
            position[current] = len(path)
            path.append(current)
            current = outgoing[current][0]["receiver_id"]
        if current in position:
            cycle = path[position[current]:]
            if len(cycle) >= 2:
                total = checked_integer(sum(outgoing[employee][0]["gift_value"] for employee in cycle))
                combinations.add((len(cycle), total))
        visited.update(path)
    return [
        {"chain_id": index + 1, "chain_length": length, "total_gift_value": value}
        for index, (length, value) in enumerate(sorted(combinations, reverse=True))
    ]
