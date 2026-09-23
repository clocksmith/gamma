"""Common disjoint intersections, with unchanged native trajectories per arm."""
import math
import struct
from pathlib import Path
from .fx2_trajectory_costs_v1 import analyze
from .fx2_coverage_preservation_v1 import target_sets, partition_name


def costs(prefix, tokens, plan):
    base=analyze(prefix,tokens,plan['training']['narrow_starts'],250000)
    masks=target_sets(plan);bins={};prefix=str(prefix)
    bits=Path(prefix+'.bits').read_bytes()
    for row,(_,_,_,eligible,_,p) in enumerate(struct.iter_unpack('<QBBBBf',Path(prefix+'.neural').read_bytes())):
        name=partition_name(row,eligible,masks);cell=bins.setdefault(name,{'targets':0,'N':[],'F':[]})
        cell['targets']+=1
        if eligible:cell['N'].append(-math.log2(p))
        for i in range(8):
            q,truth=struct.unpack_from('<HB',bits,row*24+i*3)
            cell['F'].append(-math.log2((q if truth else 65536-q)/65536))
    result={k:{'targets':v['targets'],'neural_bits':math.fsum(v['N']) if k!='no_neural' else None,
               'final_bits':math.fsum(v['F'])} for k,v in bins.items()}
    if not math.isclose(math.fsum(v['final_bits'] for v in result.values()),base['total']['final_bits'],abs_tol=1e-7,rel_tol=0):
        raise ValueError('partition final costs do not reconcile')
    return {'partitions':result,'total':base['total'],'mask_sizes':{k:len(v) for k,v in masks.items()},
            'partition_order':['narrow','broad','preservation']}


def deltas(measurements):
    parent=measurements['P'];result={}
    for arm,row in measurements.items():
        p=row['costs'];cells={}
        for key,value in p['partitions'].items():
            other=parent['costs']['partitions'][key]
            if value['targets']!=other['targets']:raise ValueError('unmatched common partition')
            cells[key]={'targets':value['targets'],'delta_neural_bits':None if value['neural_bits'] is None else value['neural_bits']-other['neural_bits'],
                        'delta_final_bits':value['final_bits']-other['final_bits']}
        dn=p['total']['neural_bits']-parent['costs']['total']['neural_bits'];df=p['total']['final_bits']-parent['costs']['total']['final_bits']
        db=row['archive_bytes']-parent['archive_bytes']
        result[arm]={'partitions':cells,'delta_neural_bits':dn,'delta_final_bits':df,'archive_delta_bytes':db,
                     'packed_delta_bytes':row['packed_bytes']-parent['packed_bytes'],
                     'component_delta_bytes':row['component_bytes']-parent['component_bytes'],'coding_residual_bits':8*db-df}
    return result
