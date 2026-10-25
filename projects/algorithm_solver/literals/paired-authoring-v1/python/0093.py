class Solution:
    def restoreIpAddresses(self, s: str) -> list[str]:
        if len(s) < 4 or len(s) > 12:
            return []

        addresses = []
        parts = []

        def collect(start: int) -> None:
            slots = 4 - len(parts)
            remaining = len(s) - start
            if remaining < slots or remaining > 3 * slots:
                return
            if slots == 0:
                addresses.append(".".join(parts))
                return

            value = 0
            for end in range(start, min(start + 3, len(s))):
                if end > start and s[start] == "0":
                    break
                value = value * 10 + ord(s[end]) - 48
                if value > 255:
                    break
                parts.append(s[start:end + 1])
                collect(end + 1)
                parts.pop()

        collect(0)
        return addresses
