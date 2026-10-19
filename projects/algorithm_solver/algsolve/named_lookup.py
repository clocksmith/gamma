"""Opt-in named-output query adapter for an explicitly bound source catalog.

Use this module's CLI/API for named-output catalogs; the ordinary answer CLI
never silently enables this adapter. The original catalog remains untouched.
"""
import argparse
import hashlib
import json
from pathlib import Path
from . import named_output_contracts
from .answer import answer as base_answer
from .approved_library import load_context as base_load_context
from .records import Problem


def adapter_record():
    return {'id':'algsolve.named-output.v3','module':'algsolve.named_output_contracts','entrypoint':'bind',
        'module_sha256':hashlib.sha256(Path(named_output_contracts.__file__).read_bytes()).hexdigest(),
        'wrapper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def check_adapter(catalog):
    if catalog.manifest.get('query_adapter')!=adapter_record():
        raise ValueError('Catalog is not bound to this named-output adapter')


def load_context(path):
    context,catalog=base_load_context(path)
    check_adapter(catalog)
    return context,catalog


def answer(context,query,*,approved_library):
    check_adapter(approved_library)
    return base_answer(context,named_output_contracts.bind(query),approved_library=approved_library)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query',type=Path,help='JSON Problem with public examples')
    parser.add_argument('--approved-library',type=Path,required=True,help='Catalog explicitly bound to this adapter')
    args=parser.parse_args();context,catalog=load_context(args.approved_library)
    query=Problem.from_dict(json.loads(args.query.read_text()))
    print(json.dumps(answer(context,query,approved_library=catalog),ensure_ascii=False))

if __name__=='__main__':main()
