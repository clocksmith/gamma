"""Original Hack2Hire 6945a578e85c245612a9786f variant over an INFERRED specification; qualification unknown."""


def solve(relationships, employee):
    manager = {}
    for row in relationships:
        for report in row[1:]:
            manager[report] = row[0]
    chain = [employee]
    while chain[-1] in manager:
        chain.append(manager[chain[-1]])
    chain.reverse()
    return chain


class Solution:
    def reportChain(self, relationships, employee):
        return solve(relationships, employee)
