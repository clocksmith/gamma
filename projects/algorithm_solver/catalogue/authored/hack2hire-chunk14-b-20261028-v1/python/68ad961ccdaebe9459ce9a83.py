"""Hack2Hire 68ad961ccdaebe9459ce9a83 (Auto Email Generation) over an INFERRED spec; qualification unknown."""


def solve(detectedWords, categories, username):
    category_of = {keyword: category for keyword, category in categories}
    grouped = {}
    for word in detectedWords:
        category = category_of.get(word)
        if category is None:
            continue
        counts = grouped.setdefault(category, {})
        counts[word] = counts.get(word, 0) + 1
    lines = ['Dear ' + username + ',']
    if not grouped:
        lines.append('No violations found.')
    for category in sorted(grouped):
        lines.append(category + ': ' + ', '.join('%s (%d)' % (w, c) for w, c in grouped[category].items()))
    return '\n'.join(lines)


class Solution:
    def generateEmail(self, detectedWords, categories, username):
        return solve(detectedWords, categories, username)
