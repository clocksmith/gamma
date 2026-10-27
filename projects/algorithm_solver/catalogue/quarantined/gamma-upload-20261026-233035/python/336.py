"""336. Palindrome Pairs."""
def solve(words: list[str]) -> list[list[int]]:
    indices = {word: index for index, word in enumerate(words)}
    result = []
    for index, word in enumerate(words):
        for split in range(len(word) + 1):
            left, right = word[:split], word[split:]
            if left == left[::-1]:
                candidate = right[::-1]
                if candidate in indices and indices[candidate] != index:
                    result.append([indices[candidate], index])
            if split < len(word) and right == right[::-1]:
                candidate = left[::-1]
                if candidate in indices and indices[candidate] != index:
                    result.append([index, indices[candidate]])
    return result

class Solution:
    def palindromePairs(self, words: list[str]) -> list[list[int]]:
        return solve(words)
