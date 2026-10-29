"""Original candidate; no qualification or admission."""

from bisect import bisect_right

class TimeMap:
    def __init__(self):self.records={}
    def set(self,key,value,timestamp):
        times,values=self.records.setdefault(key,([],[]));times.append(timestamp);values.append(value)
    def get(self,key,timestamp):
        if key not in self.records:return ''
        times,values=self.records[key];i=bisect_right(times,timestamp)-1
        return values[i] if i>=0 else ''


def solve(operations, arguments):
    instance = TimeMap(*arguments[0])
    out = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        out.append(getattr(instance, operation)(*values))
    return out
