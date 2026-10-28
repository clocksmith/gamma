"""Host-only independent cases. Generated packets are private, never source files."""
import importlib.util
from pathlib import Path


def load(name):
    spec = importlib.util.spec_from_file_location('continuation_a_'+name, Path(__file__).with_name(name+'.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_cases(pid, include_analytic_boundaries=True):
    oracle, controls = load('oracles'), load('test_oracles')
    if type(pid) is not int or pid not in oracle.IDS:
        raise ValueError('fixed assigned identity required')
    rows, seen = [], set()
    def add(args, answer, category):
        import json
        oracle.validate(pid,args)
        key=json.dumps(args,sort_keys=True,separators=(',',':'))
        if key in seen:
            return
        seen.add(key)
        rows.append({'args':args,'expected':answer,'compare':'return','category':category})
    for args, answer in controls.EXAMPLES[pid]:
        if oracle.expected(pid,args)!=answer:
            raise ValueError('independent reference/public example disagreement')
        add(args,answer,'official-numeric-example')
    for identity,args in oracle.synthetic_cases():
        if identity==pid:
            add(args,oracle.expected(pid,args),'seeded-independent-bounded-reference')
    if not include_analytic_boundaries:
        return rows
    if pid==3623:
        points=[[x,y] for y in (0,1) for x in range(50000)]
        pair=50000*49999//2
        add([points],pair*pair%oracle.MOD,'maximum-two-horizontal-lines-product-certificate')
    elif pid==3625:
        add([[[i,1000] for i in range(500)]],0,'maximum-collinear-no-convex-quadrilateral')
        add([[[-1000,-1000],[1000,-1000],[-1000,1000],[1000,1000]]],1,'numeric-extreme-single-convex-rectangle')
    elif pid==3627:
        add([[10**9]*499998],166666*10**9,'maximum-valid-length-uniform-every-median-fixed')
    elif pid==3628:
        left,middle,right=33333,33333,33334
        add(['L'*left+'C'*middle+'T'*right],left*middle*right+max(middle*right,left*middle,left*right),'maximum-three-block-insertion-certificate')
    elif pid==3629:
        add([[1]*100000],99999,'maximum-no-prime-path-distance')
        add([[2]+[1]*99998+[1000000]],1,'maximum-one-direct-prime-teleport-edge')
    elif pid==3634:
        add([[10**9]*100000,100000],0,'maximum-uniform-array-no-removal')
    elif pid==3635:
        add([[100000]*50000 for _ in range(4)],300000,'maximum-equal-opening-and-duration')
    elif pid==3638:
        add([[2,1]*50000],50000,'maximum-alternating-pairs-upper-bound-n-over-two')
        add([[10**9]*100000],0,'maximum-equal-values-strict-balance-impossible')
    elif pid==3644:
        permutation=list(range(100000));permutation[65534],permutation[65535]=65535,65534
        add([permutation],65534,'maximum-single-required-swap-and-certificate')
    else:
        add([[100000]*100000,[100000]*100000],10**10,'maximum-all-items-activate-before-final-threshold')
        add([[100000]*100000,[1]*100000],100000,'maximum-one-activation-retires-all-items')
    return rows
