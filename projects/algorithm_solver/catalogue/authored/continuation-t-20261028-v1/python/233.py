class Solution:
    def countDigitOne(self, n):
        answer = 0
        factor = 1
        while factor <= n:
            high = n // (factor * 10)
            current = (n // factor) % 10
            low = n % factor
            answer += high * factor
            if current == 1:
                answer += low + 1
            elif current > 1:
                answer += factor
            factor *= 10
        return answer
