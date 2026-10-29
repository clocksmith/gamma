"""Original hack2hire:688fe380b3f942cc1004c02a; inferred public-preview contract; qualification unknown."""
def eliminateAdjacentDuplicates(text):
    previous, run, changes = None, 0, 0
    for char in text:
        if char == previous:
            run += 1
        else:
            previous, run = char, 1
        if run % 2 == 0:
            changes += 1
    return changes

solve = eliminateAdjacentDuplicates

class Solution:
    eliminateAdjacentDuplicates = staticmethod(eliminateAdjacentDuplicates)
