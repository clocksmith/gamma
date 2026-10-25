class Solution:
    def finalString(self, s: str) -> str:
        left = []
        right = []
        reversed_order = False
        for character in s:
            if character == "i":
                reversed_order = not reversed_order
            elif reversed_order:
                left.append(character)
            else:
                right.append(character)
        if reversed_order:
            right.reverse()
            return "".join(right) + "".join(left)
        left.reverse()
        return "".join(left) + "".join(right)
