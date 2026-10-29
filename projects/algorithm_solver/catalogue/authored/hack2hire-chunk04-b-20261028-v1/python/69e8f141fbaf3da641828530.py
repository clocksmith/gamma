"""Hack2Hire 69e8f141fbaf3da641828530 (Correct Bedroom Counts from Descriptions) over an INFERRED spec; qualification unknown."""
import re

SEPARATORS = re.compile('[^a-z0-9]+')


def words(text):
    """Maximal runs of ASCII letters and digits, lower-cased (descriptions are printable ASCII)."""
    return [w for w in SEPARATORS.split(text.lower()) if w]


def classify(text):
    w = words(text)
    studio = 'studio' in w
    one = any(x == '1br' or x == '1bd' for x in w) or any(w[i] in ('1', 'one') and w[i + 1] == 'bedroom' for i in range(len(w) - 1))
    if studio and not one:
        return 0
    if one and not studio:
        return 1
    return -1


def solve(descriptions, numBedrooms):
    result = []
    for text, recorded in zip(descriptions, numBedrooms):
        kind = classify(text)
        result.append(recorded if kind < 0 else kind)
    return result


class Solution:
    def correctBedrooms(self, descriptions, numBedrooms):
        return solve(descriptions, numBedrooms)
