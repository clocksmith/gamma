#!/usr/bin/env python3
"""Writes the private side files for v3: problem groups and lexer-class cuts.

A cut before byte p means bytes p-1 and p have different lexical classes, the same
rule v1 and v2 used to label an entry as crossing a boundary.

    prepare.py <v1 private folder> <side folder> <acorn.js>
"""
import hashlib
import io
import json
import keyword
import subprocess
import sys
import tokenize
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE.parent / 'fixed-source-v1' / 'manifest.json'


def python_classes(raw):
    text = raw.decode('latin1')
    marks = ['l' if ch in '\r\n' else 'w' for ch in text]
    starts = [0]
    for index, ch in enumerate(text):
        if ch == '\n':
            starts.append(index + 1)
    at = lambda position: starts[position[0] - 1] + position[1]

    def paint(start, end, letter):
        for index in range(at(start), at(end)):
            if text[index] not in '\r\n' or letter in 'sc':
                marks[index] = letter

    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        kind = tokenize.tok_name[token.type]
        if kind == 'NAME':
            letter = 'k' if keyword.iskeyword(token.string) else 'i'
        elif kind == 'NUMBER':
            letter = 'n'
        elif kind in ('STRING', 'FSTRING_START', 'FSTRING_MIDDLE', 'FSTRING_END'):
            letter = 's'
        elif kind == 'COMMENT':
            letter = 'c'
        elif kind == 'OP':
            letter = 'p'
        else:
            continue
        paint(token.start, token.end, letter)
    line_start = True
    for index, mark in enumerate(marks):
        if mark == 'l':
            line_start = True
        elif line_start and mark == 'w':
            marks[index] = 't'
        else:
            line_start = False
    return ''.join(marks)


def cut_map(marks):
    out = bytearray(len(marks))
    for at in range(1, len(marks)):
        if marks[at] != marks[at - 1]:
            out[at] = 1
    return bytes(out)


def main():
    private, side, acorn = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    side.mkdir(mode=0o700, parents=True, exist_ok=True)
    rows = json.loads(MANIFEST.read_text())['problems']
    listing = private / 'lists' / 'javascript.txt'
    js_paths = listing.read_text().split()
    js_marks = json.loads(subprocess.run(['node', str(private / 'lex.cjs'), acorn, str(listing)],
                                         capture_output=True, check=True).stdout)
    parts = {'python': [], 'javascript': []}
    for index, row in enumerate(rows):
        for language, extension in (('python', 'py'), ('javascript', 'js')):
            raw = (private / 'sources' / language / f"{row['id']}.{extension}").read_bytes()
            if hashlib.sha256(raw).hexdigest() != row[language]:
                raise SystemExit('hash mismatch')
            marks = python_classes(raw) if language == 'python' else js_marks[js_paths[index]]
            if len(marks) != len(raw):
                raise SystemExit('class map length differs from source')
            parts[language].append(cut_map(marks))
    report = {}
    views = {'python': (parts['python'], list(range(400))), 'javascript': (parts['javascript'], list(range(400))),
             'both': (parts['python'] + parts['javascript'], list(range(400)) * 2)}
    for name, (maps, groups) in views.items():
        joined = b''.join(maps)
        (side / f'{name}.cuts').write_bytes(joined)
        (side / f'{name}.groups').write_text('\n'.join(map(str, groups)) + '\n')
        report[name] = {'bytes': len(joined), 'cuts': sum(joined), 'cuts_sha256': hashlib.sha256(joined).hexdigest()}
    (side / 'side.json').write_text(json.dumps(report, indent=1) + '\n')
    print(report)


if __name__ == '__main__':
    main()
