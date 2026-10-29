"""Hack2Hire 691e30e108ad7861624b56aa (Music Player, level 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class MusicPlayer:
    def __init__(self):
        self.titles = [None]
        self.listeners = [None]
        self.recent = {}

    def addSong(self, title):
        self.titles.append(title)
        self.listeners.append(set())
        return len(self.titles) - 1

    def playSong(self, songId, userId):
        self.listeners[songId].add(userId)
        user = self.recent.get(userId)
        if user is None:
            user = self.recent[userId] = {'head': 0, 'next': {}, 'prev': {}}
        if songId in user['next']: self._unlink(user, songId)
        head = user['head']
        user['next'][songId], user['prev'][songId] = head, 0
        if head: user['prev'][head] = songId
        user['head'] = songId

    def getAnalytics(self):
        live = [i for i in range(1, len(self.titles))]
        live.sort(key=lambda i: (-len(self.listeners[i]), i))
        return [[self.titles[i], len(self.listeners[i])] for i in live]

    def _unlink(self, user, song):
        nxt, prv = user['next'], user['prev']
        before, after = prv.pop(song), nxt.pop(song)
        if before: nxt[before] = after
        else: user['head'] = after
        if after: prv[after] = before

    def getLastThreeSongs(self, userId):
        user = self.recent.get(userId)
        result = []
        if user is None: return result
        song = user['head']
        while song and len(result) < 3:
            after = user['next'][song]
            result.append(song)
            song = after
        return result


def solve(operation_names, argument_lists):
    if operation_names[0] != 'MusicPlayer' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = MusicPlayer()
    allowed = {'addSong', 'playSong', 'getAnalytics', 'getLastThreeSongs'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        result.append(getattr(instance, name)(*arguments))
    return result
