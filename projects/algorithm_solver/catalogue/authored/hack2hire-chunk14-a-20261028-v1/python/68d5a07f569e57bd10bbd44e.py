"""Hack2Hire 68d5a07f569e57bd10bbd44e (Text Box Formatter, variant 3 of 3) over an INFERRED spec; qualification unknown."""


def _wrap(sentence, width):
    lines, current, size = [], [], 0
    for word in sentence.split(' '):
        if current and size + 1 + len(word) <= width:
            current.append(word)
            size += 1 + len(word)
        else:
            if current:
                lines.append(current)
            current, size = [word], len(word)
    lines.append(current)
    return lines


def _justify(words, width):
    gaps = len(words) - 1
    spaces = width - sum(len(w) for w in words)
    base, extra = divmod(spaces, gaps)
    parts = [words[0]]
    for g in range(gaps):
        parts.append(' ' * (base + (1 if g < extra else 0)))
        parts.append(words[g + 1])
    return ''.join(parts)


def solve(sentences, maxWidth):
    border = '+' + '-' * maxWidth + '+'
    out = []
    for sentence in sentences:
        lines = _wrap(sentence, maxWidth)
        out.append(border)
        for i, words in enumerate(lines):
            if i < len(lines) - 1 and len(words) > 1:
                line = _justify(words, maxWidth)
            else:
                line = ' '.join(words).ljust(maxWidth)
            out.append('|' + line + '|')
        out.append(border)
    return out


class Solution:
    def formatJustifiedBoxes(self, sentences, maxWidth):
        return solve(sentences, maxWidth)
