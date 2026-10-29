"""Hack2Hire 67d44fdf488516fd8ad5a0ba (Design Recent File Tracker) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

from bisect import insort

INVERT = str.maketrans('0123456789', '9876543210')  # inverted date digits sort newest first
BLOCK = 512


class FileStorageSystem:
    def __init__(self):
        self.blocks = []  # sorted blocks of keys "<inverted date><name>"; together one sorted sequence
        self.inserted = []

    def storeFile(self, file, date):
        key = date.translate(INVERT) + file
        self.inserted.append(file)
        blocks = self.blocks
        if not blocks:
            blocks.append([key])
            return
        i = 0
        while i < len(blocks) - 1 and blocks[i][-1] < key:
            i += 1
        block = blocks[i]
        insort(block, key)
        if len(block) > 2 * BLOCK:
            blocks[i:i + 1] = [block[:BLOCK], block[BLOCK:]]

    def getKthRecentFiles(self, k):
        out = []
        for block in self.blocks:
            need = k - len(out)
            if need <= 0:
                break
            out.extend(key[10:] for key in block[:need])
        return out

    def returnAllFiles(self):
        return list(self.inserted)


def solve(operation_names, argument_lists):
    if operation_names[0] != 'FileStorageSystem' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = FileStorageSystem(*argument_lists[0])
    allowed = {'storeFile', 'getKthRecentFiles', 'returnAllFiles'}
    voids = {'storeFile'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
