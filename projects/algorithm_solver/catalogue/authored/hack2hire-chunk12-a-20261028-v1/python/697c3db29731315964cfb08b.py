"""Hack2Hire 697c3db29731315964cfb08b (Linked User Records by Similarity, variant 1 of 3) over an INFERRED spec; qualification unknown."""


def _units(text):
    whole, _, frac = text.partition('.')
    return int(whole) * 10000 + int((frac + '0000')[:4])


def _scorer(records, weights, threshold):
    """Exact integer weights (ten-thousandths), value buckets per weighted field, and a per-row score function."""
    header, rows = records[0], records[1:]
    fields = []
    for item in weights:
        name, value = item.split(':')
        w = _units(value)
        if w:
            fields.append((header.index(name), w))
    buckets = []
    for k, _ in fields:
        by_value = {}
        for j, row in enumerate(rows):
            if row[k] != '':
                by_value.setdefault(row[k], []).append(j)
        buckets.append(by_value)

    def scores(i):
        score = [0] * len(rows)
        row = rows[i]
        for (k, w), by_value in zip(fields, buckets):
            if row[k] != '':
                for j in by_value[row[k]]:
                    score[j] += w
        return score
    return rows, header.index('id'), scores, _units(str(threshold))


def solve(records, weights, threshold):
    rows, idc, scores, t = _scorer(records, weights, threshold)
    out = []
    for i in range(len(rows)):
        score = scores(i)
        for j in range(i + 1, len(rows)):
            if score[j] >= t:
                out.append([rows[i][idc], rows[j][idc]])
    return out


class Solution:
    def linkedPairs(self, records, weights, threshold):
        return solve(records, weights, threshold)
