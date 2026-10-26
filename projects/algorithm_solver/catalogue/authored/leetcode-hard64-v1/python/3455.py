"""3455. Shortest Matching Substring: KMP occurrence lists joined with monotone pointers."""


def solve(s: str, p: str) -> int:
    """O(|s| + |p|) time and O(|s| + |p|) auxiliary space. Inputs are preserved."""
    parts = p.split('*')

    def occurrences(pattern):
        if not pattern:
            return list(range(len(s) + 1))
        failure = [0] * len(pattern)
        matched = 0
        for index in range(1, len(pattern)):
            while matched and pattern[index] != pattern[matched]:
                matched = failure[matched - 1]
            if pattern[index] == pattern[matched]:
                matched += 1
            failure[index] = matched
        result = []
        matched = 0
        for index, character in enumerate(s):
            while matched and character != pattern[matched]:
                matched = failure[matched - 1]
            if character == pattern[matched]:
                matched += 1
            if matched == len(pattern):
                result.append(index - len(pattern) + 1)
                matched = failure[matched - 1]
        return result

    first, second, third = [occurrences(part) for part in parts]
    second_index = third_index = 0
    answer = len(s) + 1
    for start in first:
        while second_index < len(second) and second[second_index] < start + len(parts[0]):
            second_index += 1
        if second_index == len(second):
            break
        middle_end = second[second_index] + len(parts[1])
        while third_index < len(third) and third[third_index] < middle_end:
            third_index += 1
        if third_index == len(third):
            break
        answer = min(answer, third[third_index] + len(parts[2]) - start)
    return answer if answer <= len(s) else -1


class Solution:
    def shortestMatchingSubstring(self, s: str, p: str) -> int:
        return solve(s, p)
