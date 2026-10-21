def count_connected_components(adjacency_matrix: list[list[int]]) -> int:
    node_count = len(adjacency_matrix)
    visited_nodes = ([False] * node_count)
    component_count = 0
    for start_index in range(node_count):
        if (not visited_nodes[start_index]):
            component_count += 1
            visited_nodes[start_index] = True
            pending_indices = [start_index]
            while pending_indices:
                node_index = pending_indices.pop()
                for neighbor_index in range(node_count):
                    if (adjacency_matrix[node_index][neighbor_index] and (not visited_nodes[neighbor_index])):
                        visited_nodes[neighbor_index] = True
                        pending_indices.append(neighbor_index)
    return component_count

class Solution:
    def findCircleNum(self, isConnected: list[list[int]]) -> int:
        return count_connected_components(isConnected)
