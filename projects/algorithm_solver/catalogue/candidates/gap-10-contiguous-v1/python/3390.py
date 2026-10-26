"""3390. Longest Team Pass Streak

Authored candidate. Not executed, syntax-checked, tested, or qualified.
Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
Signature: solve(teams, passes).
O(players + passes log passes) time; O(players + passes) space.
Sender-team-local streaks; an intercepted outgoing pass breaks that team's run. Matches the consulted query's positive-streak-only result set. Same-time passes use pass_from ascending as an explicit mock tie rule, not a verified Gamma rule.
Specification: https://leetcode.com/problems/longest-team-pass-streak/description/
Consulted reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3300-3399/3390.Longest%20Team%20Pass%20Streak/README_EN.md
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
    by_team = {}
    for item in passes:
        if item["pass_from"] not in by_player or item["pass_to"] not in by_player:
            continue
        by_team.setdefault(by_player[item["pass_from"]], []).append(item)
    result = []
    for team, events in by_team.items():
        events.sort(key=lambda row: (match_time(row["time_stamp"]), row["pass_from"]))
        current = longest = 0
        for event in events:
            current = current + 1 if by_player[event["pass_to"]] == team else 0
            longest = max(longest, current)
        if longest > 0:
            result.append({"team_name": team, "longest_streak": longest})
    return sorted(result, key=lambda row: row["team_name"])
