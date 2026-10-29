"""Original Hack2Hire 6a2091c38b879849ebc118ad variant over an INFERRED specification; qualification unknown."""


def solve(logs):
    journeys = {}
    for user, stamp, action in logs:
        journeys.setdefault(user, []).append((len(stamp), stamp, action))
    root = {}
    for events in journeys.values():
        events.sort()
        node = root
        for _, _, action in events:
            child = node.setdefault(action, [0, {}])
            child[0] += 1
            node = child[1]
    lines, stack = [], [(action, child, 0) for action, child in sorted(root.items(), reverse=True)]
    while stack:
        action, (count, children), depth = stack.pop()
        lines.append('  ' * depth + action + ' (' + str(count) + ')')
        stack.extend((a, c, depth + 1) for a, c in sorted(children.items(), reverse=True))
    return lines


class Solution:
    def userJourneyTrie(self, logs):
        return solve(logs)
