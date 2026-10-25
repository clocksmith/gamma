class Solution:
    def canConvert(self, source, target):
        if source == target:
            return True
        mapping = {}
        for index, character in enumerate(source):
            replacement = target[index]
            if character in mapping and mapping[character] != replacement:
                return False
            mapping[character] = replacement
        return len(set(target)) < 26
