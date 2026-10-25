"""Development runner: receives inputs only, never expected results.

This executes this batch's reviewed sources, not arbitrary untrusted code.
A fresh subprocess and parent timeout are isolation aids, not a security sandbox.
"""
import json
import runpy
import sys
from pathlib import Path


def containers(value):
    if isinstance(value, (list, dict)):
        yield id(value)
        for item in (value if isinstance(value, list) else value.values()):
            yield from containers(item)


def main():
    root = Path(__file__).resolve().parent
    functions = {}
    answers = []
    for row in json.load(sys.stdin):
        pid = str(row['id'])
        if not pid.isascii() or not pid.isdecimal():
            raise ValueError('Expected a numeric problem ID')
        if pid not in functions:
            functions[pid] = runpy.run_path(str(root / 'python' / (pid + '.py')))['solve']
        args = row['args']
        before = json.dumps(args, sort_keys=True)
        input_objects = set(containers(args))
        result = functions[pid](*args)
        answers.append({'result': result,
                        'unchanged': json.dumps(args, sort_keys=True) == before,
                        'aliases_input': bool(input_objects.intersection(containers(result)))})
    json.dump(answers, sys.stdout, allow_nan=False)
    sys.stdout.write('\n')


if __name__ == '__main__':
    main()
