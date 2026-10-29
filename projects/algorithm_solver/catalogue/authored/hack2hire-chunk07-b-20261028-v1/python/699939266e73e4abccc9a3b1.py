"""Hack2Hire 699939266e73e4abccc9a3b1 (Newspaper Text Alignment) over an INFERRED spec; qualification unknown."""

def solve(paragraphs, aligns, width):
    page = ['*' * (width + 2)]
    for words, align in zip(paragraphs, aligns):
        lines, current, length = [], [], 0
        for word in words:
            if current and length + 1 + len(word) > width:
                lines.append(' '.join(current))
                current, length = [], 0
            length = len(word) if not current else length + 1 + len(word)
            current.append(word)
        lines.append(' '.join(current))
        for line in lines:
            pad = ' ' * (width - len(line))
            page.append('*' + (line + pad if align == 'LEFT' else pad + line) + '*')
    page.append('*' * (width + 2))
    return page


class Solution:
    def formatPage(self, paragraphs, aligns, width):
        return solve(paragraphs, aligns, width)
