class Solution:
    def areSentencesSimilar(self, sentence1: list[str], sentence2: list[str], similarPairs: list[list[str]]) -> bool:
        if len(sentence1) != len(sentence2):
            return False

        neighbors = {}
        for left, right in similarPairs:
            if left not in neighbors:
                neighbors[left] = set()
            if right not in neighbors:
                neighbors[right] = set()
            neighbors[left].add(right)
            neighbors[right].add(left)
        for index, left in enumerate(sentence1):
            right = sentence2[index]
            if left == right:
                continue
            if left not in neighbors or right not in neighbors[left]:
                return False
        return True
