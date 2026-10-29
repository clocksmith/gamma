"""Literal small-trace references, independent of the affine/pointer candidates."""
MOD = 1000000007

def validate_domain(pid, args):
    operations, rows = args
    assert type(operations) is list and type(rows) is list and len(operations) == len(rows) and operations
    def integer(x, lo, hi):
        assert type(x) is int and lo <= x <= hi
    if pid == 1622:
        assert operations[0] == 'Fancy' and rows[0] == []
        assert len(operations) - 1 <= 100000
        for operation, row in zip(operations[1:], rows[1:]):
            assert operation in ('append', 'addAll', 'multAll', 'getIndex') and type(row) is list and len(row) == 1
            integer(row[0], 0 if operation == 'getIndex' else 1, 100000 if operation == 'getIndex' else 100)
    elif pid == 1656:
        assert operations[0] == 'OrderedStream' and len(rows[0]) == 1
        n = rows[0][0]
        integer(n, 1, 1000)
        assert len(operations) == n + 1
        used = set()
        for operation, row in zip(operations[1:], rows[1:]):
            assert operation == 'insert' and type(row) is list and len(row) == 2
            idx, value = row
            integer(idx, 1, n)
            assert idx not in used
            used.add(idx)
            assert type(value) is str and len(value) == 5 and all('a' <= c <= 'z' for c in value)
    else:
        raise ValueError(pid)

def reference(pid, args):
    validate_domain(pid, args)
    operations, rows = args
    result = [None]
    if pid == 1622:
        sequence = []
        for operation, row in zip(operations[1:], rows[1:]):
            x = row[0]
            if operation == 'append':
                sequence.append(x)
                result.append(None)
            elif operation == 'addAll':
                sequence = [(v+x) % MOD for v in sequence]
                result.append(None)
            elif operation == 'multAll':
                sequence = [v*x % MOD for v in sequence]
                result.append(None)
            else:
                result.append(sequence[x] if x < len(sequence) else -1)
    else:
        n = rows[0][0]
        arrived = {}
        emitted = set()
        for operation, (idx, value) in zip(operations[1:], rows[1:]):
            arrived[idx] = value
            # Recompute the initial fully arrived prefix from scratch, then take its not-yet-emitted suffix.
            prefix = next((i for i in range(1,n+1) if i not in arrived), n+1)
            chunk = [arrived[i] for i in sorted(arrived) if i < prefix and i not in emitted]
            emitted.update(i for i in arrived if i < prefix)
            result.append(chunk)
    return result
