"""Original shortest-parent DAG variant with leaf-only answer path copies."""


class Solution:
    def findLadders(self, beginWord, endWord, wordList):
        words = [beginWord]
        index_by_word = {beginWord: 0}
        for word in wordList:
            if word not in index_by_word:
                index_by_word[word] = len(words)
                words.append(word)
        target = index_by_word.get(endWord)
        if target is None:
            return []

        distance = [-1] * len(words)
        distance[0] = 0
        parents = [[] for _ in words]
        queue = [0]
        head = 0
        target_depth = -1
        alphabet = 'abcdefghijklmnopqrstuvwxyz'
        length = len(beginWord)
        while head < len(queue):
            node = queue[head]
            head += 1
            if target_depth != -1 and distance[node] >= target_depth:
                break
            word = words[node]
            next_depth = distance[node] + 1
            for position in range(length):
                prefix, suffix = word[:position], word[position + 1:]
                for letter in alphabet:
                    if letter == word[position]:
                        continue
                    neighbor = index_by_word.get(prefix + letter + suffix)
                    if neighbor is None:
                        continue
                    if distance[neighbor] == -1:
                        distance[neighbor] = next_depth
                        queue.append(neighbor)
                    if distance[neighbor] == next_depth:
                        parents[neighbor].append(node)
                        if neighbor == target:
                            target_depth = next_depth
        if target_depth == -1:
            return []

        answers = []
        reverse_path = [target]
        parent_cursor = [0]
        while reverse_path:
            node = reverse_path[-1]
            if node == 0:
                answers.append([words[index] for index in reversed(reverse_path)])
                reverse_path.pop()
                parent_cursor.pop()
                continue
            offset = parent_cursor[-1]
            if offset == len(parents[node]):
                reverse_path.pop()
                parent_cursor.pop()
                continue
            parent_cursor[-1] = offset + 1
            reverse_path.append(parents[node][offset])
            parent_cursor.append(0)
        return answers
