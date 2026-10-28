"""Existing Q140 independent cases plus a new closed zero-answer certificate."""
import importlib.util
from pathlib import Path
ORIGINAL=Path(__file__).resolve().parent.parent/'continuation-q-20261028-v1'

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
reference=load(ORIGINAL/'oracles.py','q140_original_reference')
generator=load(ORIGINAL/'cases.py','q140_original_case_owner')


def unreachable_prefix_certificate(args):
    reference.validate_domain(140,args)
    text,words=args
    if all(not text.startswith(word) for word in words):return []
    raise ValueError('zero-answer prefix certificate does not apply')


def build_cases():
    rows=[{**row,'inherited_q_case_index':index} for index,row in enumerate(generator.build_cases(140,include_maximum=True))]
    args=['b'+'a'*19,['a'*size for size in range(1,11)]]
    rows.append({'args':args,'expected':unreachable_prefix_certificate(args),'category':'closed-unreachable-start-dense-suffix',
                 'certificate':'No dictionary word matches the required first prefix; no complete segmentation exists.',
                 'isolate':True,'comparison':{'kind':'unordered-distinct-sequences','duplicates_forbidden':True}})
    return rows
