"""Hack2Hire 68961c873a1d9e6d6042d57a (Design In-memory Database with Backup, variant 2 of 4) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class InMemoryDB:
    def __init__(self):
        self.records = {}

    def setData(self, key, field, value):
        self.records.setdefault(key, {})[field] = value

    def getData(self, key, field):
        record = self.records.get(key)
        if record is None:
            return ''
        return record.get(field, '')

    def deleteData(self, key, field):
        record = self.records.get(key)
        if record is None or field not in record:
            return False
        del record[field]
        if not record:
            del self.records[key]
        return True

    def scanData(self, key):
        return self.scanDataByPrefix(key, '')

    def scanDataByPrefix(self, key, prefix):
        record = self.records.get(key)
        if record is None:
            return []
        names = sorted(f for f in record if f.startswith(prefix))
        return [f + '(' + record[f] + ')' for f in names]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'InMemoryDB' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = InMemoryDB(*argument_lists[0])
    allowed = {'setData', 'getData', 'deleteData', 'scanData', 'scanDataByPrefix'}
    voids = {'setData'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
