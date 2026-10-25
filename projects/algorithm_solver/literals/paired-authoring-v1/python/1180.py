class Solution:
    def countLetters(self, text):
        previous = None
        run_length = 0
        total = 0
        for character in text:
            if character == previous:
                run_length += 1
            else:
                run_length = 1
            total += run_length
            previous = character
        return total
