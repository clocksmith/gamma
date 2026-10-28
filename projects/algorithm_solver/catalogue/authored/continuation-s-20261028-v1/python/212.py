class Solution:
    def findWords(self, board, words):
        trie = {}
        for word in words:
            node = trie
            for c in word:
                node = node.setdefault(c, {})
            node[None] = word
        m, n = len(board), len(board[0])
        visited = [[False] * n for _ in range(m)]
        result = []
        def walk(r, c, parent):
            char = board[r][c]
            node = parent.get(char)
            if node is None:
                return
            word = node.pop(None, None)
            if word is not None:
                result.append(word)
            visited[r][c] = True
            for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if 0 <= rr < m and 0 <= cc < n and not visited[rr][cc] and board[rr][cc] in node:
                    walk(rr, cc, node)
            visited[r][c] = False
            if not node:
                del parent[char]
        for r in range(m):
            for c in range(n):
                walk(r, c, trie)
        return result
