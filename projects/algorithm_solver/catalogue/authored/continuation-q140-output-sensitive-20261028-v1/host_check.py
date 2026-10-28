"""Repair-local certificate bridge; the frozen Q observer/checker stays unchanged."""
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
cases=load(HERE/'cases.py','q140_frozen_zero_certificate')
original=load(HERE.parents[1]/'continuation-q-observers-20261028-v1/host_check.py','q140_unchanged_q_checker')


def expected(pid,args):
    if type(pid) is not int or pid!=140:raise ValueError('fixed140 repair only')
    try:return cases.unreachable_prefix_certificate(args)
    except ValueError:return original.expected(pid,args)


def check_observation(pid,args,record,language):
    try:
        if type(pid) is not int or pid!=140:return False,'wrong_repair_identity'
        try:cases.unreachable_prefix_certificate(args)
        except ValueError:return original.check_observation(pid,args,record,language)
        if language not in ('python','javascript') or type(record) is not dict or 'error' in record:return False,'observation_shape'
        entry='python-solution-method' if language=='python' else 'javascript-official-function'
        if record.get('native_route')!='official-wrapper-q-v1' or record.get('entry_kind')!=entry or type(record.get('problem_id')) is not int or record['problem_id']!=140 or record.get('method')!='wordBreak':return False,'official_route'
        if not original.exact(record.get('args_before'),args) or not original.exact(record.get('args_after'),args) or not original.exact(record.get('alias_edges'),[]) or record.get('node_identity') is not None or record.get('node_integrity') is not None:return False,'ordinary_effects'
        if record.get('result_type')!=('list' if language=='python' else 'object') or not original.exact(record.get('result'),[]):return False,'zero_certificate_result'
        return True,None
    except (ValueError,TypeError,KeyError,IndexError):return False,'invalid_repair_observation'
