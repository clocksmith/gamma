"""Decode one complete program without injecting wrappers or helpers."""
import argparse,sys
from pathlib import Path
from bitpack import decode
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('dictionary',type=Path);p.add_argument('program',type=Path);p.add_argument('--output',type=Path)
a=p.parse_args();source=decode(a.dictionary.read_bytes(),a.program.read_bytes())
if a.output:a.output.write_bytes(source.encode('utf-8'))
else:sys.stdout.write(source)
