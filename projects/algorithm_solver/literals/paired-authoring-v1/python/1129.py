class Solution:
    def shortestAlternatingPaths(self, n: int, redEdges: list[list[int]], blueEdges: list[list[int]]) -> list[int]:
        edges = [[[] for _ in range(n)] for _ in range(2)]
        for first, second in redEdges:
            edges[0][first].append(second)
        for first, second in blueEdges:
            edges[1][first].append(second)
        distance = [[-1, -1] for _ in range(n)]
        distance[0] = [0, 0]
        queue = [(0, 0), (0, 1)]
        head = 0
        while head < len(queue):
            node, previous_color = queue[head]
            head += 1
            next_color = 1 - previous_color
            for neighbor in edges[next_color][node]:
                if distance[neighbor][next_color] == -1:
                    distance[neighbor][next_color] = distance[node][previous_color] + 1
                    queue.append((neighbor, next_color))
        output = []
        for red_distance, blue_distance in distance:
            if red_distance == -1:
                output.append(blue_distance)
            elif blue_distance == -1:
                output.append(red_distance)
            else:
                output.append(min(red_distance, blue_distance))
        return output
