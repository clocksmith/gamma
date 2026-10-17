"""Host-owned validators for functional tasks with non-unique valid outputs."""


def topological_order(args, observed):
    if (len(args) != 2 or type(args[0]) is not int or args[0] < 0
            or not isinstance(args[1], list)):
        raise ValueError('Invalid course-order input')
    n, edges = args
    adjacency, indegree = [[] for _ in range(n)], [0] * n
    for edge in edges:
        if (not isinstance(edge, list) or len(edge) != 2
                or any(type(v) is not int or not 0 <= v < n for v in edge)):
            raise ValueError('Invalid course prerequisite')
        course, prerequisite = edge
        adjacency[prerequisite].append(course)
        indegree[course] += 1
    # An empty answer is valid only when no complete order exists (or n == 0).
    ready = [i for i in range(n) if indegree[i] == 0]
    for vertex in ready:
        for neighbor in adjacency[vertex]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                ready.append(neighbor)
    if len(ready) != n:
        return observed == []
    if (not isinstance(observed, list) or len(observed) != n
            or any(type(v) is not int or not 0 <= v < n for v in observed)
            or len(set(observed)) != n):
        return False
    position = {vertex: i for i, vertex in enumerate(observed)}
    return all(position[prerequisite] < position[course] for course, prerequisite in edges)


VALIDATORS = {'topological_order': topological_order}
