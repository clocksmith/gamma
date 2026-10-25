def solve(text):
    left = 0
    right = len(text) - 1
    while left < right and text[left] == text[right]:
        boundary = text[left]
        while left <= right and text[left] == boundary:
            left += 1
        while right >= left and text[right] == boundary:
            right -= 1
    return right - left + 1
