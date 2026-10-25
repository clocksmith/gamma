class Solution:
    def checkIfExist(self, arr: list[int]) -> bool:
        seen = set()
        for value in arr:
            if 2 * value in seen:
                return True
            if value % 2 == 0 and value // 2 in seen:
                return True
            seen.add(value)
        return False
