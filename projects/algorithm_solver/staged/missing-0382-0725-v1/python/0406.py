"""406. Queue Reconstruction by Height. Insert descending heights at their required rank; preserves input arrays."""

def solve(people: list[list[int]]) -> list[list[int]]:
    answer = []
    for person in sorted(people, key=lambda item: (-item[0], item[1])):
        answer.insert(person[1], person[:])
    return answer


class Solution:
    def reconstructQueue(self, people: list[list[int]]) -> list[list[int]]:
        return solve(people)
