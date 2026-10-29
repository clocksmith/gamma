"""Hack2Hire 685637ce4d16ce2ead6e1769 (Encode And Decode) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class Codec:
    @staticmethod
    def _flush(pending, runs):
        for k in range(0, len(pending), 8):
            chunk = pending[k:k + 8]
            width = max(1, max(chunk).bit_length())
            runs.append('BP[' + ', '.join([str(width)] + [str(v) for v in chunk]) + ']')
        pending.clear()

    def encode(self, nums):
        runs, pending = [], []
        i, n = 0, len(nums)
        while i < n:
            j = i
            while j < n and nums[j] == nums[i]:
                j += 1
            if j - i >= 3:
                Codec._flush(pending, runs)
                runs.append('RLE[%d, %d]' % (nums[i], j - i))
            else:
                pending.extend(nums[i:j])
            i = j
        Codec._flush(pending, runs)
        return runs

    def decode(self, runs):
        out = []
        for run in runs:
            if run.startswith('RLE['):
                value, count = run[4:-1].split(', ')
                out.extend([int(value)] * int(count))
            else:
                out.extend(int(x) for x in run[3:-1].split(', ')[1:])
        return out


def solve(operation_names, argument_lists):
    if operation_names[0] != 'Codec' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = Codec(*argument_lists[0])
    allowed = {'encode', 'decode'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
