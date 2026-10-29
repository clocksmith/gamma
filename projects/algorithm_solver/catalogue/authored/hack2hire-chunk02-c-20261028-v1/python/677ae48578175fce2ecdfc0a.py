"""Hack2Hire 677ae48578175fce2ecdfc0a (Design Inverted Index, variant 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

import re

_WORD = re.compile(r'[a-z0-9]+')


class DocumentLibrary:
    def __init__(self, documents):
        self._ids = [document[0] for document in documents]
        self._index = {}  # word -> {document index -> set of positions}, documents inserted in order
        for number, (_, text) in enumerate(documents):
            for position, word in enumerate(_WORD.findall(text.lower())):
                self._index.setdefault(word, {}).setdefault(number, set()).add(position)

    def search(self, phrase):
        words = _WORD.findall(phrase.lower())
        if not words or any(word not in self._index for word in words):
            return []
        postings = [self._index[word] for word in words]
        result = []
        for number, starts in postings[0].items():
            rest = [posting.get(number) for posting in postings[1:]]
            if any(positions is None for positions in rest):
                continue
            if any(all(start + offset in positions for offset, positions in enumerate(rest, 1)) for start in starts):
                result.append(self._ids[number])
        return result


def solve(operation_names, argument_lists):
    if operation_names[0] != 'DocumentLibrary':
        raise ValueError('exact initial constructor required')
    instance = DocumentLibrary(*argument_lists[0])
    allowed = ['search']
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        result.append(getattr(instance, name)(*arguments))
    return result
