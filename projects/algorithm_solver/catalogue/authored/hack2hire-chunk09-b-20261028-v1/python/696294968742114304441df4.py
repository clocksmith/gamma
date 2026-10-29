"""Hack2Hire 696294968742114304441df4 (Company Role Assignment) over an INFERRED spec; qualification unknown."""


def solve(existingAssociations, newAssociations):
    triples = set()
    roles = set()
    for company, contact, role in existingAssociations:
        triples.add((company, contact, role))
        roles.add((company, role))
    out = []
    for company, contact, role in newAssociations:
        if (company, contact, role) in triples:
            out.append('ALREADY_EXISTS')
        elif (company, role) in roles:
            out.append('ROLE_TAKEN')
        else:
            out.append('VALID')
            triples.add((company, contact, role))
            roles.add((company, role))
    return out


class Solution:
    def validateAssociations(self, existingAssociations, newAssociations):
        return solve(existingAssociations, newAssociations)
