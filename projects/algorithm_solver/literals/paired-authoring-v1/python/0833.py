class Solution:
    def findReplaceString(self, s: str, indices: list[int], sources: list[str], targets: list[str]) -> str:
        matches = {}
        for operation, index in enumerate(indices):
            if s.startswith(sources[operation], index):
                matches[index] = operation
        result = []
        index = 0
        while index < len(s):
            if index in matches:
                operation = matches[index]
                result.append(targets[operation])
                index += len(sources[operation])
            else:
                result.append(s[index])
                index += 1
        return "".join(result)
