def solve(text):
    index = 0
    while index < len(text) and text[index] == " ":
        index += 1
    sign = 1
    if index < len(text) and text[index] in "+-":
        if text[index] == "-":
            sign = -1
        index += 1
    value = 0
    limit = 2147483648 if sign < 0 else 2147483647
    while index < len(text) and "0" <= text[index] <= "9":
        value = value * 10 + ord(text[index]) - 48
        if value >= limit:
            return sign * limit
        index += 1
    return sign * value
