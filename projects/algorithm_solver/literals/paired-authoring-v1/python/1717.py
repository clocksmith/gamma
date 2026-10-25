def remove_pair(characters: list[str], first: str, second: str, value: int):
    stack = []
    score = 0
    for character in characters:
        if stack and stack[-1] == first and character == second:
            stack.pop()
            score += value
        else:
            stack.append(character)
    return stack, score


class Solution:
    def maximumGain(self, s: str, x: int, y: int) -> int:
        characters = list(s)
        if x >= y:
            remaining, first_score = remove_pair(characters, "a", "b", x)
            _, second_score = remove_pair(remaining, "b", "a", y)
        else:
            remaining, first_score = remove_pair(characters, "b", "a", y)
            _, second_score = remove_pair(remaining, "a", "b", x)
        return first_score + second_score
