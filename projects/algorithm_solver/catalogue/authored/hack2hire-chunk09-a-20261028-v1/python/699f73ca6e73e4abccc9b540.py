"""Hack2Hire 699f73ca6e73e4abccc9b540 (Caesar Cipher Rotation) over an INFERRED spec; qualification unknown."""


def solve(message, shift):
    s = shift % 26
    table = {}
    for i in range(26):
        table[ord('a') + i] = chr(ord('a') + (i + s) % 26)
        table[ord('A') + i] = chr(ord('A') + (i + s) % 26)
    return message.translate(table)


class Solution:
    def rotateMessage(self, message, shift):
        return solve(message, shift)
