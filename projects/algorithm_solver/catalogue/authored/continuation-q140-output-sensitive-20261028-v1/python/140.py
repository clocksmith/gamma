"""Original output-sensitive Word Break II variant with charged trie matching."""


class Solution:
    def wordBreak(self, s, wordDict):
        children = [[-1] * 26]
        terminal = [None]
        maximum_word_length = 0
        for word in wordDict:
            maximum_word_length = max(maximum_word_length, len(word))
            node = 0
            for character in word:
                letter = ord(character) - 97
                following = children[node][letter]
                if following == -1:
                    following = len(children)
                    children[node][letter] = following
                    children.append([-1] * 26)
                    terminal.append(None)
                node = following
            terminal[node] = word

        length = len(s)
        edges = [[] for _ in range(length)]
        for start in range(length):
            node = 0
            for end in range(start, min(length, start + maximum_word_length)):
                node = children[node][ord(s[end]) - 97]
                if node == -1:
                    break
                word = terminal[node]
                if word is not None:
                    edges[start].append((end + 1, word))

        can_finish = [False] * (length + 1)
        can_finish[length] = True
        for start in range(length - 1, -1, -1):
            can_finish[start] = any(can_finish[end] for end, _ in edges[start])
        if not can_finish[0]:
            return []
        for start in range(length):
            edges[start] = [edge for edge in edges[start] if can_finish[edge[0]]]

        answers = []
        path = []

        def emit(start):
            if start == length:
                answers.append(' '.join(path))
                return
            for end, word in edges[start]:
                path.append(word)
                emit(end)
                path.pop()

        emit(0)
        return answers
