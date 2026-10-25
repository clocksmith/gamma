class Solution:
    def numUniqueEmails(self, emails: list[str]) -> int:
        addresses = set()
        for email in emails:
            local, domain = email.split("@")
            local = local.split("+", 1)[0].replace(".", "")
            addresses.add(local + "@" + domain)
        return len(addresses)
