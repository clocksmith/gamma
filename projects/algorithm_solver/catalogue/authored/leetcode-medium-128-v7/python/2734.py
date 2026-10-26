"""2734. Lexicographically Smallest String After Substring Operation: decrease the first non-a run or wrap the final a when every character is a."""


def solve(s: str) -> str:
    """O(n) time and O(n) auxiliary space; inputs are read-only."""
    characters = list(s)
    index = 0
    while index < len(characters) and characters[index] == 'a':
        index += 1
    if index == len(characters):
        characters[-1] = 'z'
    else:
        while index < len(characters) and characters[index] != 'a':
            characters[index] = chr(ord(characters[index]) - 1)
            index += 1
    return ''.join(characters)


class Solution:
    def smallestString(self, s: str) -> str:
        return solve(s)
