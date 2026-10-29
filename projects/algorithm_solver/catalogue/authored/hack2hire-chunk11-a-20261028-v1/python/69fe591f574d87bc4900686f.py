"""Hack2Hire 69fe591f574d87bc4900686f (Format Articles Within Width) over an INFERRED spec; qualification unknown."""


def solve(articles, maxWidth):
    lines = []
    for index, article in enumerate(articles):
        if index:
            lines.append('')
        words = article.split(' ')
        start, length = 0, len(words[0])
        for i in range(1, len(words)):
            if length + 1 + len(words[i]) <= maxWidth:
                length += 1 + len(words[i])
            else:
                lines.append(' '.join(words[start:i]))
                start, length = i, len(words[i])
        lines.append(' '.join(words[start:]))
    return lines


class Solution:
    def formatArticles(self, articles, maxWidth):
        return solve(articles, maxWidth)
