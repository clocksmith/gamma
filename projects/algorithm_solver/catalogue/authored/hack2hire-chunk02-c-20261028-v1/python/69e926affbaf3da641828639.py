"""Hack2Hire 69e926affbaf3da641828639 (Convert Snake Case to Camel Case, variant 1) over an INFERRED spec; qualification unknown."""

import re

_RUN = re.compile(r'[A-Za-z0-9_]+')
_WORD = re.compile(r'[a-z0-9]+')


def _convert(match):
    run = match.group(0)
    core = run.lstrip('_')
    words = core.split('_')
    if len(words) < 2 or not all(_WORD.fullmatch(word) for word in words) or not 'a' <= core[0] <= 'z':
        return run
    return run[:len(run) - len(core)] + words[0] + ''.join(word[0].upper() + word[1:] for word in words[1:])


def solve(src):
    return _RUN.sub(_convert, src)


class Solution:
    def snakeToCamel(self, src):
        return solve(src)
