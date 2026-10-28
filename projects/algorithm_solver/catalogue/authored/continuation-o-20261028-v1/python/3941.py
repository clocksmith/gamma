"""Original frontend 3941 variant; qualification unknown."""

def solve(password):
    total = 0
    for char in set(password):
        if 'a' <= char <= 'z':
            total += 1
        elif 'A' <= char <= 'Z':
            total += 2
        elif '0' <= char <= '9':
            total += 3
        else:
            total += 5
    return total


class Solution:
    def passwordStrength(self, password):
        return solve(password)
