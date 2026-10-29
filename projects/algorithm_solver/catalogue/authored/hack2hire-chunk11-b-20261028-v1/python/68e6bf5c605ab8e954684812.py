"""Hack2Hire 68e6bf5c605ab8e954684812 (Friendship and Balance Tracker) over an INFERRED spec; qualification unknown."""


def _pair(a, b):
    return (a, b) if a < b else (b, a)


def solve(requests):
    balance = {}   # user -> balance
    pending = {}   # sequence number of a friend request -> (from, to)
    friends = set()  # ordered user pairs
    out = []
    for seq, request in requests:
        parts = request.split('/')
        kind = parts[1]
        if kind == 'REGISTER':
            if parts[2] in balance:
                out.append('ERROR')
            else:
                balance[parts[2]] = int(parts[3])
                out.append('OK')
        elif kind == 'FRIEND_REQUEST':
            a, b = parts[2], parts[3]
            if a not in balance or b not in balance or a == b or _pair(a, b) in friends:
                out.append('ERROR')
            else:
                pending[seq] = (a, b)
                out.append('OK')
        elif kind == 'ACCEPT_FRIEND_REQUEST':
            request_pair = pending.pop(parts[2], None)
            if request_pair is None:
                out.append('ERROR')
            else:
                friends.add(_pair(*request_pair))
                out.append('OK')
        elif kind == 'TRANSFER':
            a, b, amount = parts[2], parts[3], int(parts[4])
            if a in balance and b in balance and a != b and _pair(a, b) in friends and balance[a] >= amount:
                balance[a] -= amount
                balance[b] += amount
                out.append('OK')
            else:
                out.append('ERROR')
        else:
            out.append(str(balance[parts[2]]) if parts[2] in balance else 'ERROR')
    return out


class Solution:
    def processRequests(self, requests):
        return solve(requests)
