"""3384. Team Dominance by Pass Success

Authored candidate. Not executed, syntax-checked, tested, or qualified.
Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
Signature: solve(teams, passes).
O(players + passes + groups log groups) time; O(players + groups) space.
45:00 belongs to half 1; 45:01 starts half 2. Emits observed sender-team/half groups, as in the consulted GROUP BY solution; it does not manufacture zero-pass groups. Unknown-player passes do not join.
Specification: https://leetcode.com/problems/team-dominance-by-pass-success/description/
Consulted reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3300-3399/3384.Team%20Dominance%20by%20Pass%20Success/README_EN.md
"""

import re

def match_time(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{2}:[0-9]{2}", value):
        raise TypeError("Expected a normalized MM:SS match timestamp.")
    minutes, seconds = map(int, value.split(":"))
    if seconds > 59 or minutes > 90 or (minutes == 90 and seconds != 0):
        raise ValueError("Match timestamp is outside 00:00 through 90:00.")
    return minutes * 60 + seconds

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
            elif kind == "time":
                match_time(value)
                valid = True
            if not valid:
                raise TypeError("Invalid value for column: " + column)
        key = tuple(row[column] for column in primary_key)
        if key in seen:
            raise ValueError("Duplicate primary key.")
        seen.add(key)

def solve(teams, passes):
    validate_rows(teams, {'player_id': 'int', 'team_name': 'str'}, ['player_id'])
    validate_rows(passes, {'pass_from': 'int', 'time_stamp': 'time', 'pass_to': 'int'}, ['pass_from', 'time_stamp'])
    by_player = {row["player_id"]: row["team_name"] for row in teams}
    scores = {}
    for item in passes:
        if item["pass_from"] not in by_player or item["pass_to"] not in by_player:
            continue
        team = by_player[item["pass_from"]]
        half = 1 if match_time(item["time_stamp"]) <= 45 * 60 else 2
        key = (team, half)
        scores[key] = scores.get(key, 0) + (1 if team == by_player[item["pass_to"]] else -1)
    return [
        {"team_name": team, "half_number": half, "dominance": score}
        for (team, half), score in sorted(scores.items())
    ]
