"""Explicit source-bound SortedList runtime, layered on the named-output route.

Only a manifest's selected stored sources receive the optional backend. All
other answers execute the original checker, with no extra attempt or global
monkeypatch. Use this CLI/API explicitly; older routes/catalogs are unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path
from . import answer as answer_module
from . import dependency_bundle,named_lookup,named_output_contracts
from .approved_library import code_hash,digest,selected_reference
from .dependency_judge import isolated_function,make_public_checker
from .records import Problem

_MODULES=('dependency_bundle.py','dependency_harness.py','dependency_judge.py','dependency_lookup.py')


def profile_record(sources):
    if (not isinstance(sources,dict) or not sources or any(not isinstance(k,str) or not k.startswith('lc:')
            or not isinstance(v,str) or len(v)!=64 or any(c not in '0123456789abcdef' for c in v)
            for k,v in sources.items())):
        raise ValueError('Invalid dependency source bindings')
    return {'id':'algsolve.sortedcontainers-2.4.0.v1','wheel_sha256':dependency_bundle.SHA256,
        'wheel_bytes':dependency_bundle.SIZE,'task_file':dependency_bundle.TASK_NAME,
        'sources':dict(sources),'modules_sha256':{name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in _MODULES}}


def check_profile(catalog):
    profile=catalog.manifest.get('runtime_dependency')
    if not isinstance(profile,dict) or profile!=profile_record(profile.get('sources')):
        raise ValueError('Catalog is not bound to this dependency runtime')
    return profile


def make_answer(sources):
    # This factory receives manifest-selected stored-source hashes, never test
    # contents or an evaluator target. The original answer function still picks
    # the source and enforces its identity/approval/public-example gates.
    profile_record(sources)
    dependency_checker=make_public_checker()
    frozen_sources=dict(sources)
    def check_stored(query,entry,wall_seconds):
        expected=frozen_sources.get(entry.key)
        if expected is None:return answer_module.check_stored(query,entry,wall_seconds)
        reference=selected_reference(entry)
        if reference is None or code_hash(reference['code'])!=expected:
            raise ValueError('Dependency selected-source identity mismatch')
        return dependency_checker(query,entry,wall_seconds)
    return isolated_function(answer_module.answer,{'check_stored':check_stored},allowed={'check_stored'})


def load_context(path):
    context,catalog=named_lookup.load_context(path)
    profile=check_profile(catalog)
    for key,expected in profile['sources'].items():
        if key not in context.lookup.by_key:raise ValueError('Dependency source missing from catalog index')
        entry=context.entries[context.lookup.by_key[key]];reference=selected_reference(entry)
        if reference is None or code_hash(reference['code'])!=expected:
            raise ValueError('Dependency source bytes changed')
    context._dependency_profile_digest=digest(profile)
    context._dependency_bound_answer=make_answer(profile['sources'])
    return context,catalog


def answer(context,query,*,approved_library):
    profile=check_profile(approved_library)
    if getattr(context,'_dependency_profile_digest',None)!=digest(profile):
        raise ValueError('Context was not loaded for this dependency profile')
    return context._dependency_bound_answer(context,named_output_contracts.bind(query),approved_library=approved_library)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query',type=Path,help='JSON Problem with public examples')
    parser.add_argument('--approved-library',type=Path,required=True,help='Explicit dependency-bound source catalog')
    args=parser.parse_args();context,catalog=load_context(args.approved_library)
    query=Problem.from_dict(json.loads(args.query.read_text()))
    print(json.dumps(answer(context,query,approved_library=catalog),ensure_ascii=False))

if __name__=='__main__':main()
