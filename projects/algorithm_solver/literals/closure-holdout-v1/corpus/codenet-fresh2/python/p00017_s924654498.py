import sys
for s in map(lambda l: list(l.rstrip()), sys.stdin.readlines()):
    while True:
        for i, c in enumerate(s):
            char_code = ord(c)
            if 97 <= char_code <= 122:
                char_code = char_code+1 if char_code < 122 else 97
                s[i] = chr(char_code)

        _s = "".join(s)
        if "this" in _s or "the" in _s or "that" in _s:
            print(_s)
            break