class Solution:
    def defangIPaddr(self, address: str) -> str:
        result = []
        for character in address:
            if character == ".":
                result.append("[.]")
            else:
                result.append(character)
        return "".join(result)
