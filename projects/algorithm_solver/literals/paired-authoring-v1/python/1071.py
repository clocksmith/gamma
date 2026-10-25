class Solution:
    def gcdOfStrings(self, str1: str, str2: str) -> str:
        first = len(str1)
        second = len(str2)
        while second != 0:
            first, second = second, first % second
        period = first
        for index in range(len(str1)):
            if str1[index] != str1[index % period]:
                return ""
        for index in range(len(str2)):
            if str2[index] != str1[index % period]:
                return ""
        return str1[:period]
