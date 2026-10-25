class Solution:
    def findRestaurant(self, list1: list[str], list2: list[str]) -> list[str]:
        positions = {}
        for index, name in enumerate(list2):
            positions[name] = index
        best_sum = len(list1) + len(list2)
        result = []
        for index, name in enumerate(list1):
            if name not in positions:
                continue
            index_sum = positions[name] + index
            if index_sum < best_sum:
                best_sum = index_sum
                result = [name]
            elif index_sum == best_sum:
                result.append(name)
        return result
