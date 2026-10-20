import importlib.util
from pathlib import Path
p=Path(__file__).with_name('search.py');spec=importlib.util.spec_from_file_location('literal_search',p);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
sources={'a':{'x':'const solve = (values) => (values.length);\n'},'b':{'x':'function solve(values) { return values[0]; }\n'}}
assert not module.admissible(sources['a']['x'],sources)
assert not module.admissible('(values) => (values.length)',sources)
assert module.admissible('values',sources)
assert module.admissible('values.length',sources)
assert not module.admissible('not-in-any-source',sources)
print('5 fragment-admission checks passed')
