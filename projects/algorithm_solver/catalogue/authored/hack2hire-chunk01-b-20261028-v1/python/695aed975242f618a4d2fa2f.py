"""Hack2Hire 695aed975242f618a4d2fa2f (Design a Buffered File Writer). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown."""


class BufferedFile:
    """Fixed-capacity byte buffer; each call returns the bytes handed to the sink during that call."""

    def __init__(self, capacity, file=None):
        self.capacity = capacity
        self.buffer = [0] * capacity
        self.size = 0
        self.file = file

    def _drain(self, out):
        chunk = self.buffer[:self.size]
        if self.file is not None:
            for byte in chunk:
                self.file.write(byte)
        out.extend(chunk)
        self.size = 0

    def write(self, data):
        out = []
        i, n = 0, len(data)
        while i < n:
            take = min(self.capacity - self.size, n - i)
            self.buffer[self.size:self.size + take] = data[i:i + take]
            self.size += take
            i += take
            if self.size == self.capacity:
                self._drain(out)
        return out

    def flush(self):
        out = []
        if self.size:
            self._drain(out)
        return out


def solve(operation_names, argument_lists):
    if operation_names[0] != 'BufferedFile' or len(argument_lists[0]) != 1:
        raise ValueError('exact initial constructor required')
    instance = BufferedFile(argument_lists[0][0])
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name == 'write':
            result.append(instance.write(arguments[0]))
        elif name == 'flush' and not arguments:
            result.append(instance.flush())
        else:
            raise ValueError('unknown method')
    return result
