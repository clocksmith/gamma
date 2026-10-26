"""929. Unique Email Addresses (Easy).

Specification: https://leetcode.com/problems/unique-email-addresses/description/
"""


def solve(emails: list[str]) -> int:
    """O(total characters) expected time and space; normalize only the local part."""
    addresses = set()
    for email in emails:
        local, domain = email.split('@')
        local = local.split('+', 1)[0].replace('.', '')
        addresses.add(local + '@' + domain)
    return len(addresses)


class Solution:
    def numUniqueEmails(self, emails: list[str]) -> int:
        return solve(emails)
