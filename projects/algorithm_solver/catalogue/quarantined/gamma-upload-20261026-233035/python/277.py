"""277. Find the Celebrity."""
def solve(n: int, knows_fn=None) -> int:
    if knows_fn is None:
        knows_fn = globals()['knows']
    candidate = 0
    for person in range(1, n):
        if knows_fn(candidate, person):
            candidate = person
    for person in range(n):
        if person != candidate and (knows_fn(candidate, person) or not knows_fn(person, candidate)):
            return -1
    return candidate

class Solution:
    def findCelebrity(self, n: int) -> int:
        return solve(n)
