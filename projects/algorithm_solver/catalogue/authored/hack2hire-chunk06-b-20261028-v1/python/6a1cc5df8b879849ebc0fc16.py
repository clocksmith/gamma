"""Hack2Hire 6a1cc5df8b879849ebc0fc16 (Group Chat Mention Counter) over an INFERRED spec; qualification unknown."""

def solve(members, messages):
    index = {member: i for i, member in enumerate(members)}
    counts = [0] * len(members)
    everyone = 0
    for message in messages:
        hit, all_flag = set(), False
        for token in message.split(' '):
            if token.startswith('@'):
                body = token[1:]
                if body == 'all':
                    all_flag = True
                else:
                    for user in body.split(','):
                        if user in index:
                            hit.add(index[user])
        if all_flag:
            everyone += 1
        else:
            for i in hit:
                counts[i] += 1
    return [count + everyone for count in counts]


class Solution:
    def countMentions(self, members, messages):
        return solve(members, messages)
