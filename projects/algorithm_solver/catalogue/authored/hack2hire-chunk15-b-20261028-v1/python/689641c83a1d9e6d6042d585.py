"""Hack2Hire 689641c83a1d9e6d6042d585 (Design In-memory Database with Backup, variant 3 of 4) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class InMemoryDB:
    def __init__(self):
        self.records = {}

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


def solve(operation_names, argument_lists):
    if operation_names[0] != 'InMemoryDB' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = InMemoryDB(*argument_lists[0])
    allowed = {'setDataAt', 'setDataAtWithTtl', 'deleteDataAt', 'getDataAt', 'scanDataAt', 'scanDataByPrefixAt'}
    voids = {'setDataAt', 'setDataAtWithTtl'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
