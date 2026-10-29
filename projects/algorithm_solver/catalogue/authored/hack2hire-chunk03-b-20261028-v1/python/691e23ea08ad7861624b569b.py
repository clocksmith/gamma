"""Hack2Hire 691e23ea08ad7861624b569b (Music Player, level 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class MusicPlayer:
    def __init__(self):
        self.titles = [None]
        self.listeners = [None]

    def addSong(self, title):
        self.titles.append(title)
        self.listeners.append(set())
        return len(self.titles) - 1

    def playSong(self, songId, userId):
        self.listeners[songId].add(userId)

    def getAnalytics(self):
        live = [i for i in range(1, len(self.titles))]
        live.sort(key=lambda i: (-len(self.listeners[i]), i))
        return [[self.titles[i], len(self.listeners[i])] for i in live]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'MusicPlayer' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = MusicPlayer()
    allowed = {'addSong', 'playSong', 'getAnalytics'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        result.append(getattr(instance, name)(*arguments))
    return result
