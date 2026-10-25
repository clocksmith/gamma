class Solution:
    def indexPairs(self, text, words):
        children = [{}]
        terminal = [False]
        for word in words:
            node = 0
            for character in word:
                if character not in children[node]:
                    children[node][character] = len(children)
                    children.append({})
                    terminal.append(False)
                node = children[node][character]
            terminal[node] = True
        pairs = []
        for start in range(len(text)):
            node = 0
            for end in range(start, len(text)):
                character = text[end]
                if character not in children[node]:
                    break
                node = children[node][character]
                if terminal[node]:
                    pairs.append([start, end])
        return pairs
