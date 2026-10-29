"""Native official class; original development candidate, qualification pending."""
class ThroneInheritance:
    def __init__(self, kingName):
        self.king = kingName
        self.children = {kingName: []}
        self.dead = set()

    def birth(self, parentName, childName):
        self.children[parentName].append(childName)
        self.children[childName] = []

    def death(self, name):
        self.dead.add(name)

    def getInheritanceOrder(self):
        stack = [self.king]
        answer = []
        while stack:
            name = stack.pop()
            if name not in self.dead:
                answer.append(name)
            stack.extend(reversed(self.children[name]))
        return answer
