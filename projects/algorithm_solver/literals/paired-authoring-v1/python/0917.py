def is_letter(character: str) -> bool:
    return "A" <= character <= "Z" or "a" <= character <= "z"


class Solution:
    def reverseOnlyLetters(self, s: str) -> str:
        characters = list(s)
        left = 0
        right = len(characters) - 1
        while left < right:
            if not is_letter(characters[left]):
                left += 1
            elif not is_letter(characters[right]):
                right -= 1
            else:
                characters[left], characters[right] = characters[right], characters[left]
                left += 1
                right -= 1
        return "".join(characters)
