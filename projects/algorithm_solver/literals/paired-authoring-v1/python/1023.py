class Solution:
    def camelMatch(self, queries, pattern):
        def matches(query):
            index = 0
            for char in query:
                if index < len(pattern) and char == pattern[index]:
                    index += 1
                elif not ("a" <= char <= "z"):
                    return False
            return index == len(pattern)

        return [matches(query) for query in queries]
