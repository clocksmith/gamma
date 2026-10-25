def solve(equations):
    parent = list(range(26))

    def find(node):
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for equation in equations:
        if equation[1:3] == "==":
            parent[find(ord(equation[0]) - 97)] = find(ord(equation[3]) - 97)
    for equation in equations:
        if equation[1:3] == "!=":
            if find(ord(equation[0]) - 97) == find(ord(equation[3]) - 97):
                return False
    return True
