"""Hack2Hire 696feb8db7afade5b30a39ca (Business CSV Data Validator, variant 1) over an INFERRED spec; qualification unknown."""

import re

_ID = re.compile(r'[A-Za-z0-9]+')
_AMOUNT = re.compile(r'(0|[1-9][0-9]*)(\.[0-9]{2})?')
_DATE = re.compile(r'([0-9]{4})-([0-9]{2})-([0-9]{2})')
_WORD = re.compile(r'[a-z0-9]+')


def _valid_date(text):
    match = _DATE.fullmatch(text)
    if match is None:
        return False
    year, month, day = (int(part) for part in match.groups())
    if not 1900 <= year <= 2099 or not 1 <= month <= 12:
        return False
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    days = [31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]
    return 1 <= day <= days


def solve(data, forbiddenWords, ignoreWords):
    forbidden, ignore = set(forbiddenWords), set(ignoreWords)
    seen_ids, valid = set(), []
    for index in range(1, len(data)):
        fields = data[index].split(',')
        if len(fields) != 6 or any(not field or field != field.strip(' ') for field in fields):
            continue
        record_id, name, description, category, amount, day = fields
        if _ID.fullmatch(record_id) is None or record_id in seen_ids:
            continue
        if _AMOUNT.fullmatch(amount) is None or not _valid_date(day):
            continue
        words = [_WORD.findall(field.lower()) for field in (name, description, category)]
        if any(word in forbidden for group in words for word in group):
            continue
        if [w for w in words[0] if w not in ignore] == [w for w in words[1] if w not in ignore]:
            continue
        seen_ids.add(record_id)
        valid.append(index)
    return valid


class Solution:
    def validateRows(self, data, forbiddenWords, ignoreWords):
        return solve(data, forbiddenWords, ignoreWords)
