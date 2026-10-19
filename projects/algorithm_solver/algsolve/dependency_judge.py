"""Private backend adapters reuse unchanged judge/validation function bytecode.

Only named global references are replaced in new dictionaries. Original module
objects and functions are never patched. Candidate bytes, calls, comparison,
limits, stdout protocol and sandbox monitoring remain the original ones.
"""
from pathlib import Path
from types import FunctionType
from . import dependency_bundle,validate
from .judge import judge,sandbox


class _Overlay:
    def __init__(self,base,**overrides):self._base=base;self._overrides=overrides
    def __getattr__(self,name):
        return self._overrides[name] if name in self._overrides else getattr(self._base,name)


def isolated_function(original,substitutions,*,allowed):
    if set(substitutions)!=set(allowed) or not set(substitutions)<=original.__globals__.keys():
        raise ValueError('Undeclared function-global substitution')
    namespace=dict(original.__globals__);namespace.update(substitutions)
    function=FunctionType(original.__code__,namespace,original.__name__,original.__defaults__,original.__closure__)
    function.__kwdefaults__=None if original.__kwdefaults__ is None else dict(original.__kwdefaults__)
    function.__annotations__=dict(original.__annotations__)
    function.__qualname__=original.__qualname__
    return function


class BundleBackend:
    def __init__(self,data=None):
        self.data=dependency_bundle.read_bundle() if data is None else dependency_bundle.validate_bytes(data)
        self._sandbox=sandbox

    def __getattr__(self,name):return getattr(self._sandbox,name)

    def run_python(self,source_name,*,files,stdin=b'',limits=sandbox.Limits()):
        if source_name!='harness.py' or set(files)!={'harness.py','candidate.py','calls.json'}:
            raise ValueError('Unsupported dependency execution task')
        original=judge.HARNESS_PATH.read_text(encoding='utf-8')
        if files['harness.py']!=original:
            raise ValueError('Dependency adapter requires unchanged base harness')
        task=dict(files)
        task['base_harness.py']=task['harness.py']
        task['harness.py']=Path(__file__).with_name('dependency_harness.py').read_text(encoding='utf-8')
        task[dependency_bundle.TASK_NAME]=self.data
        return self._sandbox.run_python(source_name,files=task,stdin=stdin,limits=limits)


def make_judge_problem(data=None):
    backend=BundleBackend(data)
    functional=isolated_function(judge.judge_functional,{'sandbox':backend},allowed={'sandbox'})
    proxy=_Overlay(judge,judge_functional=functional)
    return isolated_function(validate.judge_problem,{'judge':proxy},allowed={'judge'})


def make_public_checker(data=None):
    from . import answer as answer_module
    proxy=_Overlay(validate,judge_problem=make_judge_problem(data))
    return isolated_function(answer_module.check_stored,{'validate':proxy},allowed={'validate'})
