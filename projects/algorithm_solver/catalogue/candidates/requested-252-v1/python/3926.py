"""3926. Count Valid Word Occurrences
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/count-valid-word-occurrences/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3926.Count%20Valid%20Word%20Occurrences/README_EN.md
Complexity: O(total text + total query characters) time and space.
ASCII lowercase words; hyphen joins only when directly between letters; chunks concatenate without separators.
"""

from __future__ import annotations
import re

def solve(chunks, queries):
    counts = {}
    for match in re.finditer(r'[a-z]+(?:-[a-z]+)*', ''.join(chunks)):
        word = match.group()
        counts[word] = counts.get(word, 0) + 1
    return [counts.get(word, 0) for word in queries]


class Solution:
    def countWordOccurrences(self, chunks, queries):
        return solve(chunks, queries)
