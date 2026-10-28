class Trie:
    def __init__(self):
        self.root = {}

    def insert(self, word):
        node = self.root
        for c in word:
            node = node.setdefault(c, {})
        node[''] = True

    def search(self, word):
        node = self.root
        for c in word:
            if c not in node:
                return False
            node = node[c]
        return '' in node

    def startsWith(self, prefix):
        node = self.root
        for c in prefix:
            if c not in node:
                return False
            node = node[c]
        return True
