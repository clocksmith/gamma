class Solution:
    def generateSentences(self, synonyms, text):
        graph = {}
        for left, right in synonyms:
            graph.setdefault(left, set()).add(right)
            graph.setdefault(right, set()).add(left)
        groups = {}
        for root in graph:
            if root in groups:
                continue
            pending = [root]
            seen = {root}
            component = []
            while pending:
                word = pending.pop()
                component.append(word)
                for neighbor in graph[word]:
                    if neighbor not in seen:
                        seen.add(neighbor)
                        pending.append(neighbor)
            component.sort()
            for word in component:
                groups[word] = component
        sentences = [""]
        for word in text.split(" "):
            expanded = []
            for prefix in sentences:
                for replacement in groups.get(word, [word]):
                    expanded.append(prefix + (" " if prefix else "") + replacement)
            sentences = expanded
        return sorted(sentences)
