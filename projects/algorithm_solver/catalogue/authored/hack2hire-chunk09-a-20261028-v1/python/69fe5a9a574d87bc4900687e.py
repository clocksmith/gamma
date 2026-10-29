"""Hack2Hire 69fe5a9a574d87bc4900687e (Account Registration Deduplication, variant 2 of 2) over an INFERRED spec; qualification unknown."""


def normal_email(email):
    local, _, domain = email.lower().partition('@')
    plus = local.find('+')
    if plus >= 0:
        local = local[:plus]
    return local.replace('.', '') + '@' + domain


def normal_phone(phone):
    return ''.join(ch for ch in phone if '0' <= ch <= '9')


def solve(names, emails, phones):
    seen_email, seen_phone, out = set(), set(), []
    for i in range(len(names)):
        e, p = normal_email(emails[i]), normal_phone(phones[i])
        if e in seen_email or p in seen_phone:
            out.append(i)
        else:
            seen_email.add(e)
            seen_phone.add(p)
    return out


class Solution:
    def findDuplicateAccounts(self, names, emails, phones):
        return solve(names, emails, phones)
