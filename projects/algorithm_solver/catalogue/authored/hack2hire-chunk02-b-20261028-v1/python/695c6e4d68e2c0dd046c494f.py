"""Original Hack2Hire 695c6e4d68e2c0dd046c494f variant over an INFERRED specification; qualification unknown."""


def solve(liveInputStream):
    index, need, out = {}, [], []
    for event in liveInputStream:
        body = event[3:]
        words = set(body.split(' '))
        if event[0] == 'Q':
            qid = len(need)
            need.append(len(words))
            for word in words:
                index.setdefault(word, []).append(qid)
            out.append('ACK: ' + body + '; ID=' + str(qid + 1))
        else:
            hits = {}
            for word in words:
                for qid in index.get(word, ()):
                    hits[qid] = hits.get(qid, 0) + 1
            matched = sorted(qid for qid, count in hits.items() if count == need[qid])
            if matched:
                out.append('M: ' + body + '; Q=' + ','.join(str(qid + 1) for qid in matched))
    return out


class Solution:
    def matchQueryLogs(self, liveInputStream):
        return solve(liveInputStream)
