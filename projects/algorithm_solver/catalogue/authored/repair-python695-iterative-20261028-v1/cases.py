"""Host-only695 cases using the existing independently designed batch05 owner."""
import importlib.util
from itertools import product
from pathlib import Path

OWNER=Path(__file__).resolve().parents[2]/'downloaded-batch05-independent-v1/oracles.py'
SPEC=importlib.util.spec_from_file_location('repair695_existing_independent_reference',OWNER)
oracle=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(oracle)


def build_cases():
    rows=[]
    def add(grid,category,known=None):
        args=[grid];oracle.validate_generated(695,args);want=oracle.expected(695,args)
        if known is not None and (type(want) is not int or want!=known):raise ValueError('independent reference certificate mismatch')
        rows.append({'args':args,'expected':want,'category':category,'compare':'return'})
    for cells in product((0,1),repeat=6):add([list(cells[:3]),list(cells[3:])],'exhaustive-two-by-three')
    add([[0]],'minimum-water',0);add([[1]],'minimum-land',1)
    add([[1]*50 for _ in range(50)],'maximum-single-component',2500)
    add([[0]*50 for _ in range(50)],'maximum-water',0)
    add([[(r+c)%2 for c in range(50)] for r in range(50)],'maximum-diagonal-disconnected',1)
    add([[1]*50],'maximum-width-row',50);add([[1] for _ in range(50)],'maximum-height-column',50)
    snake=[]
    for r in range(50):
        snake.append([1]*50 if r%2==0 else [int(c==(49 if r%4==1 else 0)) for c in range(50)])
    add(snake,'long-thin-component-depth-witness',1275)
    return rows
