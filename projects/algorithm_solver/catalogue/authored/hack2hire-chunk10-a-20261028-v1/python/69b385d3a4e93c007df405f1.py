"""Hack2Hire 69b385d3a4e93c007df405f1 (Design Note-Taking System, variant 4 of 4) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class SecondBrainSystem:
    def __init__(self):
        self.notes = {}  # note id -> record
        self.count = 0
        self.tag_index = {}  # tag -> set of note numbers

    def createNote(self, title, content, timestamp):
        self.count += 1
        note_id = 'note%d' % self.count
        self.notes[note_id] = {'n': self.count, 'title': title, 'content': content, 'created': timestamp, 'updated': timestamp, 'low': (title.lower(), content.lower()), 'tags': set(), 'versions': [(title, content)]}
        return note_id

    def getNote(self, noteId):
        rec = self.notes.get(noteId)
        return [] if rec is None else [rec['title'], rec['content'], rec['created'], rec['updated']]

    def _replace(self, rec, title, content, timestamp):
        rec['title'], rec['content'], rec['updated'] = title, content, timestamp
        rec['low'] = (title.lower(), content.lower())
        rec['versions'].append((title, content))

    def updateNote(self, noteId, title, content, timestamp):
        rec = self.notes.get(noteId)
        if rec is None:
            return False
        self._replace(rec, title, content, timestamp)
        return True

    def deleteNote(self, noteId):
        rec = self.notes.pop(noteId, None)
        if rec is None:
            return False
        for tag in rec['tags']:
            self.tag_index[tag].discard(rec['n'])
        return True

    def searchNotes(self, keyword):
        word = keyword.lower()
        hits = [(-rec['updated'], rec['n']) for rec in self.notes.values() if word in rec['low'][0] or word in rec['low'][1]]
        hits.sort()
        return ['note%d' % n for _, n in hits]

    def addTag(self, noteId, tag):
        rec = self.notes.get(noteId)
        if rec is None or tag in rec['tags']:
            return False
        rec['tags'].add(tag)
        self.tag_index.setdefault(tag, set()).add(rec['n'])
        return True

    def removeTag(self, noteId, tag):
        rec = self.notes.get(noteId)
        if rec is None or tag not in rec['tags']:
            return False
        rec['tags'].discard(tag)
        self.tag_index[tag].discard(rec['n'])
        return True

    def getNotesByTag(self, tag):
        return ['note%d' % n for n in sorted(self.tag_index.get(tag, ()))]

    def getVersionCount(self, noteId):
        rec = self.notes.get(noteId)
        return 0 if rec is None else len(rec['versions'])

    def revertNote(self, noteId, version, timestamp):
        rec = self.notes.get(noteId)
        if rec is None or not 1 <= version <= len(rec['versions']):
            return False
        title, content = rec['versions'][version - 1]
        self._replace(rec, title, content, timestamp)
        return True


def solve(operation_names, argument_lists):
    if operation_names[0] != 'SecondBrainSystem' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = SecondBrainSystem(*argument_lists[0])
    allowed = {'createNote', 'getNote', 'updateNote', 'deleteNote', 'searchNotes', 'addTag', 'removeTag', 'getNotesByTag', 'getVersionCount', 'revertNote'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
