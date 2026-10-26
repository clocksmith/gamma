"""3631. Sort Threats by Severity and Exploitability

Authored candidate. Not executed, syntax-checked, tested, or qualified.
Interface: native array candidate.
Signature: solve(threats).
O(n log n) time and O(n) auxiliary/output space.
Corrects the earlier database misclassification. This is the native array task, exposed as solve(threats), sortThreats(threats), and Solution.sortThreats(threats). Input and inner rows are preserved; score reaches 3,000,000,000, so no signed 32-bit coercion is used.
Specification: https://leetcode.com/problems/sort-threats-by-severity-and-exploitability/description/
Consulted reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3600-3699/3631.Sort%20Threats%20by%20Severity%20and%20Exploitability/README_EN.md
"""

def solve(threats):
    if not isinstance(threats, list) or not 1 <= len(threats) <= 100000:
        raise TypeError("Expected 1 through 100000 threat rows.")
    ids = set()
    result = []
    for row in threats:
        if (not isinstance(row, list) or len(row) != 3 or not all(type(value) is int for value in row)
                or not 1 <= row[0] <= 1000000 or not 1 <= row[1] <= 1000000000
                or not 1 <= row[2] <= 1000000000 or row[0] in ids):
            raise ValueError("Invalid threat row or duplicate threat ID.")
        ids.add(row[0])
        result.append(row.copy())
    return sorted(result, key=lambda row: (-(2 * row[1] + row[2]), row[0]))


def sortThreats(threats):
    return solve(threats)


class Solution:
    def sortThreats(self, threats):
        return solve(threats)
