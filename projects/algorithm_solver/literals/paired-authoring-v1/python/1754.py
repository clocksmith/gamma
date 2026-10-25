class Solution:
    def largestMerge(self, word1: str, word2: str) -> str:
        first = 0
        second = 0
        output = []
        while first < len(word1) and second < len(word2):
            if word1[first:] > word2[second:]:
                output.append(word1[first])
                first += 1
            else:
                output.append(word2[second])
                second += 1
        output.append(word1[first:])
        output.append(word2[second:])
        return "".join(output)
