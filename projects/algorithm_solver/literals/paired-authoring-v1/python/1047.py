class Solution:
    def removeDuplicates(self, s: str) -> str:
        stack = []
        for character in s:
            if stack and stack[-1] == character:
                stack.pop()
            else:
                stack.append(character)
        return "".join(stack)
