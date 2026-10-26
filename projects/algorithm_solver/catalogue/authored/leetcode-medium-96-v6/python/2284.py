"""2284. Sender With Largest Word Count: aggregate words per sender and break equal totals by the larger name."""


def solve(messages: list[str], senders: list[str]) -> str:
    """O(L + n A) time and O(n) auxiliary entries for L text characters and maximum name length A; inputs are read-only."""
    totals = {}
    for message, sender in zip(messages, senders):
        totals[sender] = totals.get(sender, 0) + message.count(' ') + 1
    best_name = ''
    best_count = -1
    for sender, count in totals.items():
        if count > best_count or (count == best_count and sender > best_name):
            best_name, best_count = sender, count
    return best_name


class Solution:
    def largestWordCount(self, messages: list[str], senders: list[str]) -> str:
        return solve(messages, senders)
