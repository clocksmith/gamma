"""420. Strong Password Checker. Allocate deletions by repeated-run lengths modulo three."""

def solve(password: str) -> int:
    missing = (not any('a' <= c <= 'z' for c in password))
    missing += not any('A' <= c <= 'Z' for c in password)
    missing += not any('0' <= c <= '9' for c in password)
    length = len(password)
    runs = []
    i = 0
    while i < length:
        j = i + 1
        while j < length and password[j] == password[i]:
            j += 1
        if j - i >= 3:
            runs.append(j - i)
        i = j
    if length < 6:
        return max(missing, 6 - length)
    replacements = sum(run // 3 for run in runs)
    if length <= 20:
        return max(missing, replacements)
    deletions = length - 20
    remaining = deletions
    use = min(remaining, sum(run % 3 == 0 for run in runs))
    replacements -= use
    remaining -= use
    use = min(remaining // 2, sum(run % 3 == 1 for run in runs))
    replacements -= use
    remaining -= 2 * use
    replacements -= min(replacements, remaining // 3)
    return deletions + max(missing, replacements)


class Solution:
    def strongPasswordChecker(self, password: str) -> int:
        return solve(password)
