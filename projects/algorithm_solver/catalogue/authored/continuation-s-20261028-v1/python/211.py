class WordDictionary:
    def __init__(self):
        self.root = {}

    def addWord(self, word):
        node = self.root
        for c in word:
            node = node.setdefault(c, {})
        node[''] = True

    def search(self, word):
        frontier = [self.root]
        for c in word:
            following = []
            for node in frontier:
                if c == '.':
                    following.extend(child for key, child in node.items() if key != '')
                elif c in node:
                    following.append(node[c])
            if not following:
                return False
            frontier = following
        return any('' in node for node in frontier)
