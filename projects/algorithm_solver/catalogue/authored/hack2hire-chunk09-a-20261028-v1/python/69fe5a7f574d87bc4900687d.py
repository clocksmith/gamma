"""Hack2Hire 69fe5a7f574d87bc4900687d (Account Registration Deduplication, variant 1 of 2) over an INFERRED spec; qualification unknown."""


def solve(names, emails, phones):
    seen_email, seen_phone, out = set(), set(), []
    for i in range(len(names)):
        e, p = emails[i], phones[i]
        if e in seen_email or p in seen_phone:
            out.append(i)
        else:
            seen_email.add(e)
            seen_phone.add(p)
    return out


class Solution:
    def findDuplicateAccounts(self, names, emails, phones):
        return solve(names, emails, phones)
