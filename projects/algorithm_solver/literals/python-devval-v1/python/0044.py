def solve(text, pattern):
    text_index = 0
    pattern_index = 0
    last_star = -1
    star_end = 0
    while text_index < len(text):
        if pattern_index < len(pattern) and pattern[pattern_index] in ("?", text[text_index]):
            text_index += 1
            pattern_index += 1
        elif pattern_index < len(pattern) and pattern[pattern_index] == "*":
            last_star = pattern_index
            star_end = text_index
            pattern_index += 1
        elif last_star >= 0:
            star_end += 1
            text_index = star_end
            pattern_index = last_star + 1
        else:
            return False
    while pattern_index < len(pattern) and pattern[pattern_index] == "*":
        pattern_index += 1
    return pattern_index == len(pattern)
