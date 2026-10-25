class Solution:
    def intervalIntersection(self, firstList: list[list[int]], secondList: list[list[int]]) -> list[list[int]]:
        first_index = 0
        second_index = 0
        output = []
        while first_index < len(firstList) and second_index < len(secondList):
            first = firstList[first_index]
            second = secondList[second_index]
            start = max(first[0], second[0])
            end = min(first[1], second[1])
            if start <= end:
                output.append([start, end])
            if first[1] < second[1]:
                first_index += 1
            else:
                second_index += 1
        return output
