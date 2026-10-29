"""Original frontend 420 variant; qualification unknown."""


def solve(password: str) -> int:
    n = len(password)
    has_lower = any("a" <= c <= "z" for c in password)
    has_upper = any("A" <= c <= "Z" for c in password)
    has_digit = any("0" <= c <= "9" for c in password)
    missing = (0 if has_lower else 1) + (0 if has_upper else 1) + (0 if has_digit else 1)

    runs = []
    i = 0
    while i < n:
        j = i
        while j < n and password[j] == password[i]:
            j += 1
        if j - i >= 3:
            runs.append(j - i)
        i = j

    if n < 6:
        return max(6 - n, missing)
    if n <= 20:
        return max(missing, sum(r // 3 for r in runs))

    deletes = n - 20
    rem = deletes
    for mod in (0, 1):
        need = mod + 1
        for idx in range(len(runs)):
            if rem < need:
                break
            if runs[idx] >= 3 and runs[idx] % 3 == mod:
                runs[idx] -= need
                rem -= need
    for idx in range(len(runs)):
        while runs[idx] >= 3 and rem >= 3:
            runs[idx] -= 3
            rem -= 3
    replacements = sum(r // 3 for r in runs if r >= 3)
    return deletes + max(missing, replacements)


strongPasswordChecker = solve


class Solution:
    def strongPasswordChecker(self, password: str) -> int:
        return solve(password)
