def solve(course_count, prerequisites):
    outgoing = [[] for _ in range(course_count)]
    indegree = [0] * course_count
    for first, second in prerequisites:
        outgoing[first - 1].append(second - 1)
        indegree[second - 1] += 1
    ready = [course for course in range(course_count) if indegree[course] == 0]
    head = 0
    semesters = 0
    completed = 0
    while head < len(ready):
        level_end = len(ready)
        semesters += 1
        while head < level_end:
            course = ready[head]
            head += 1
            completed += 1
            for following in outgoing[course]:
                indegree[following] -= 1
                if indegree[following] == 0:
                    ready.append(following)
    return semesters if completed == course_count else -1
