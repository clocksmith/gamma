"""Hack2Hire 689bb2061126a03aace65e39 (Design In-memory Database with Backup, variant 4 of 4) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class InMemoryDB:
    def __init__(self):
        self.records = {}
        self.backups = []

    def _put(self, key, field, value, expiry):
        self.records.setdefault(key, {})[field] = (value, expiry)

    def _live(self, key, field, timestamp):
        record = self.records.get(key)
        if record is None:
            return None
        item = record.get(field)
        if item is None or (item[1] is not None and timestamp >= item[1]):
            return None
        return item

    def setDataAt(self, key, field, value, timestamp):
        self._put(key, field, value, None)

    def setDataAtWithTtl(self, key, field, value, timestamp, ttl):
        self._put(key, field, value, timestamp + ttl)

    def getDataAt(self, key, field, timestamp):
        item = self._live(key, field, timestamp)
        return '' if item is None else item[0]

    def deleteDataAt(self, key, field, timestamp):
        record = self.records.get(key)
        if record is None or field not in record:
            return False
        alive = self._live(key, field, timestamp) is not None
        del record[field]
        if not record:
            del self.records[key]
        return alive

    def scanDataAt(self, key, timestamp):
        return self.scanDataByPrefixAt(key, '', timestamp)

    def scanDataByPrefixAt(self, key, prefix, timestamp):
        record = self.records.get(key)
        if record is None:
            return []
        names = sorted(f for f, (v, e) in record.items() if f.startswith(prefix) and (e is None or timestamp < e))
        return [f + '(' + record[f][0] + ')' for f in names]

    def backup(self, timestamp):
        snapshot = {}
        for key, record in self.records.items():
            kept = {}
            for field, (value, expiry) in record.items():
                if expiry is None:
                    kept[field] = (value, None)
                elif timestamp < expiry:
                    kept[field] = (value, expiry - timestamp)
            if kept:
                snapshot[key] = kept
        self.backups.append((timestamp, snapshot))
        return len(snapshot)

    def restore(self, timestamp, timestampToRestore):
        lo, hi = 0, len(self.backups)
        while lo < hi:
            mid = (lo + hi) // 2
            if self.backups[mid][0] <= timestampToRestore:
                lo = mid + 1
            else:
                hi = mid
        snapshot = self.backups[lo - 1][1]
        self.records = {}
        for key, kept in snapshot.items():
            self.records[key] = {f: (v, None if r is None else timestamp + r) for f, (v, r) in kept.items()}


def solve(operation_names, argument_lists):
    if operation_names[0] != 'InMemoryDB' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = InMemoryDB(*argument_lists[0])
    allowed = {'setDataAt', 'setDataAtWithTtl', 'deleteDataAt', 'getDataAt', 'scanDataAt', 'scanDataByPrefixAt', 'backup', 'restore'}
    voids = {'setDataAt', 'setDataAtWithTtl', 'restore'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
