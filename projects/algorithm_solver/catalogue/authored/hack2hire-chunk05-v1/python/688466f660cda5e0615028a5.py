"""Original hack2hire:688466f660cda5e0615028a5; inferred public-preview contract; qualification unknown."""
def decodePassword(text):
    x, y = (int(v.strip()) for v in text[0].strip()[1:-1].split(','))
    return text[y + 1][x]

solve = decodePassword

class Solution:
    decodePassword = staticmethod(decodePassword)
