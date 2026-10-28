"""Language-specific route gate over the unchanged independent P reference."""
import importlib.util
from pathlib import Path
S=importlib.util.spec_from_file_location('p_frozen_independent_reference',Path(__file__).resolve().parent.parent/'authored/continuation-p-20261028-v1/oracles.py')
reference=importlib.util.module_from_spec(S);S.loader.exec_module(reference)
def check_observation(pid,args,record,language):
    if language=='javascript' and record.get('entry_kind')!='javascript-official-function':return False,'official_function_entry'
    if language=='python' and 'entry_kind' in record:return False,'unexpected_entry_kind'
    return reference.check_observation(pid,args,record,language)
