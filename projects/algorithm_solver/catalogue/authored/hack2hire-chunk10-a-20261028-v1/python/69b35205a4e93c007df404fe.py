"""Hack2Hire 69b35205a4e93c007df404fe (Design Note-Taking System, variant 1 of 4) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class SecondBrainSystem:
    def __init__(self):
        self.notes = {}  # note id -> record
        self.count = 0

    def createNote(self, title, content, timestamp):
        self.count += 1
        note_id = 'note%d' % self.count
        self.notes[note_id] = {'n': self.count, 'title': title, 'content': content, 'created': timestamp, 'updated': timestamp}
        return note_id

    def getNote(self, noteId):
        rec = self.notes.get(noteId)
        return [] if rec is None else [rec['title'], rec['content'], rec['created'], rec['updated']]

    def _replace(self, rec, title, content, timestamp):
        rec['title'], rec['content'], rec['updated'] = title, content, timestamp

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
        return True


def solve(operation_names, argument_lists):
    if operation_names[0] != 'SecondBrainSystem' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = SecondBrainSystem(*argument_lists[0])
    allowed = {'createNote', 'getNote', 'updateNote', 'deleteNote'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
