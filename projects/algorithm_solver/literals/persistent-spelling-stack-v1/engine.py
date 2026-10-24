"""Unchanged46 scientific engine, bound to this isolated common adapter."""
import importlib.util
import sys
import common as c

saved=sys.modules.get('common')
try:
    sys.modules['common']=c
    spec=importlib.util.spec_from_file_location('persistent54_engine46',c.LIT/'postfit-spelling-stack-v1/engine.py')
    original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
finally:
    if saved is None:sys.modules.pop('common',None)
    else:sys.modules['common']=saved
menu=original.menu
apply=original.apply
matches=original.matches
